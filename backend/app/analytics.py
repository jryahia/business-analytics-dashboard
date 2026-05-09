from __future__ import annotations

import re
from typing import Annotated, Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Dataset, DatasetRow, User
from app.schemas import (
    AggregateRequest,
    AnalyticsResult,
    CustomAnalyticsRequest,
    PivotRequest,
    TimeSeriesRequest,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

ALLOWED_AGGFUNCS = {"sum", "mean", "count", "min", "max", "std", "median"}
SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "round": round,
    "len": len,
    "range": range,
    "list": list,
    "dict": dict,
    "str": str,
    "int": int,
    "float": float,
}


async def _load_dataframe(dataset_id: str, user_id: str, db: AsyncSession) -> pd.DataFrame:
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id)
    )
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    rows_result = await db.execute(
        select(DatasetRow.data).where(DatasetRow.dataset_id == dataset_id)
    )
    rows = [r[0] for r in rows_result.all()]
    if not rows:
        raise HTTPException(status_code=400, detail="Dataset has no rows")

    df = pd.DataFrame(rows)
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass
    return df


def _df_to_result(df: pd.DataFrame, metadata: dict[str, Any] | None = None) -> AnalyticsResult:
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    elif df.index.name:
        df = df.reset_index()

    records = df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict(orient="records")
    return AnalyticsResult(
        data=records,
        columns=list(df.columns),
        metadata=metadata or {},
    )


@router.post("/aggregate", response_model=AnalyticsResult)
async def aggregate(
    body: AggregateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsResult:
    df = await _load_dataframe(body.dataset_id, current_user.id, db)

    for col in body.group_by:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{col}' not found")

    agg_spec: dict[str, str] = {}
    for col, func in body.aggregations.items():
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{col}' not found")
        if func not in ALLOWED_AGGFUNCS:
            raise HTTPException(status_code=400, detail=f"Unsupported aggregation: {func}")
        agg_spec[col] = func

    if body.filters:
        for col, val in body.filters.items():
            if col in df.columns:
                df = df[df[col] == val]

    grouped = df.groupby(body.group_by).agg(agg_spec).reset_index()
    return _df_to_result(grouped, {"group_by": body.group_by, "aggregations": body.aggregations})


@router.post("/pivot", response_model=AnalyticsResult)
async def pivot(
    body: PivotRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsResult:
    df = await _load_dataframe(body.dataset_id, current_user.id, db)

    for col in [body.index, body.columns, body.values]:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{col}' not found")

    aggfunc = body.aggfunc if body.aggfunc in ALLOWED_AGGFUNCS else "sum"
    pivot_df = pd.pivot_table(
        df,
        index=body.index,
        columns=body.columns,
        values=body.values,
        aggfunc=aggfunc,
        fill_value=0,
    )
    pivot_df.columns = [str(c) for c in pivot_df.columns]
    return _df_to_result(pivot_df, {"index": body.index, "columns": body.columns})


@router.post("/timeseries", response_model=AnalyticsResult)
async def timeseries(
    body: TimeSeriesRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsResult:
    df = await _load_dataframe(body.dataset_id, current_user.id, db)

    if body.date_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Date column '{body.date_column}' not found")
    if body.value_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Value column '{body.value_column}' not found")

    df[body.date_column] = pd.to_datetime(df[body.date_column], errors="coerce")
    df = df.dropna(subset=[body.date_column])
    df = df.set_index(body.date_column)

    aggfunc = body.aggregation if body.aggregation in ALLOWED_AGGFUNCS else "sum"
    freq_map = {"D": "D", "W": "W", "M": "ME", "Q": "QE", "Y": "YE"}
    freq = freq_map.get(body.frequency, "D")

    resampled = df[body.value_column].resample(freq).agg(aggfunc).reset_index()
    resampled.columns = [body.date_column, body.value_column]
    resampled[body.date_column] = resampled[body.date_column].astype(str)

    return _df_to_result(resampled, {"frequency": body.frequency, "aggregation": aggfunc})


_SAFE_PATTERN = re.compile(r"^df[\.\[][\w\s\'\"\[\]\(\)\.,=<>!&|%\+\-\*\/]+$")


@router.post("/custom", response_model=AnalyticsResult)
async def custom_analytics(
    body: CustomAnalyticsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsResult:
    if not _SAFE_PATTERN.match(body.expression.strip()):
        raise HTTPException(status_code=400, detail="Expression must start with 'df.' or 'df[' and contain only safe operations")

    df = await _load_dataframe(body.dataset_id, current_user.id, db)
    local_ns: dict[str, Any] = {"df": df, "pd": pd, "np": np, **SAFE_BUILTINS}

    try:
        result = eval(body.expression.strip(), {"__builtins__": {}}, local_ns)  # noqa: S307
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Expression error: {exc}") from exc

    if isinstance(result, pd.DataFrame):
        return _df_to_result(result, {"expression": body.expression})
    elif isinstance(result, pd.Series):
        return _df_to_result(result.reset_index(), {"expression": body.expression})
    else:
        raise HTTPException(status_code=400, detail="Expression must return a DataFrame or Series")
