from __future__ import annotations

import io
from typing import Annotated, Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Chart, Dataset, DatasetRow, User
from app.schemas import ChartGenerateRequest, ChartResponse

router = APIRouter(prefix="/api/charts", tags=["charts"])

DARK_LAYOUT = dict(
    paper_bgcolor="#0f172a",
    plot_bgcolor="#1e293b",
    font={"color": "#e2e8f0", "family": "Inter, sans-serif"},
    xaxis={"gridcolor": "#334155", "linecolor": "#475569"},
    yaxis={"gridcolor": "#334155", "linecolor": "#475569"},
    margin={"l": 40, "r": 40, "t": 60, "b": 40},
)

PLOTLY_COLORS = px.colors.qualitative.Bold


async def _load_df(dataset_id: str, user_id: str, db: AsyncSession) -> pd.DataFrame:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    rows_result = await db.execute(select(DatasetRow.data).where(DatasetRow.dataset_id == dataset_id))
    rows = [r[0] for r in rows_result.all()]
    df = pd.DataFrame(rows)
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            pass
    return df


def _apply_aggregation(df: pd.DataFrame, x_col: str, y_col: str, agg: str | None, color_col: str | None) -> pd.DataFrame:
    if not agg or agg == "none":
        return df
    group_cols = [x_col] + ([color_col] if color_col and color_col in df.columns else [])
    if y_col not in df.columns:
        return df
    agg_map = {"sum": "sum", "mean": "mean", "count": "count", "min": "min", "max": "max"}
    func = agg_map.get(agg, "sum")
    return df.groupby(group_cols)[y_col].agg(func).reset_index()


def _build_figure(df: pd.DataFrame, req: ChartGenerateRequest) -> go.Figure:
    color_col = req.color_column if req.color_column and req.color_column in df.columns else None
    x_col = req.x_column
    y_col = req.y_column

    if x_col not in df.columns or y_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Columns '{x_col}' or '{y_col}' not found in dataset")

    chart_type = req.chart_type.lower()

    if chart_type == "bar":
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=req.title or f"{y_col} by {x_col}", color_discrete_sequence=PLOTLY_COLORS)
    elif chart_type == "line":
        fig = px.line(df, x=x_col, y=y_col, color=color_col, title=req.title or f"{y_col} over {x_col}", color_discrete_sequence=PLOTLY_COLORS)
    elif chart_type == "pie":
        fig = px.pie(df, names=x_col, values=y_col, title=req.title or f"{y_col} distribution", color_discrete_sequence=PLOTLY_COLORS)
    elif chart_type == "scatter":
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=req.title or f"{x_col} vs {y_col}", color_discrete_sequence=PLOTLY_COLORS)
    elif chart_type == "area":
        fig = px.area(df, x=x_col, y=y_col, color=color_col, title=req.title or f"{y_col} area over {x_col}", color_discrete_sequence=PLOTLY_COLORS)
    elif chart_type == "heatmap":
        if color_col:
            pivot = df.pivot_table(index=x_col, columns=color_col, values=y_col, aggfunc="sum", fill_value=0)
            fig = px.imshow(pivot, title=req.title or "Heatmap", color_continuous_scale="Blues")
        else:
            corr = df.select_dtypes(include=[np.number]).corr()
            fig = px.imshow(corr, title=req.title or "Correlation Heatmap", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
    elif chart_type == "histogram":
        fig = px.histogram(df, x=x_col, color=color_col, title=req.title or f"{x_col} distribution", color_discrete_sequence=PLOTLY_COLORS)
    elif chart_type == "box":
        fig = px.box(df, x=x_col, y=y_col, color=color_col, title=req.title or f"{y_col} box plot", color_discrete_sequence=PLOTLY_COLORS)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported chart type: {chart_type}")

    fig.update_layout(**DARK_LAYOUT)
    return fig


@router.post("/generate", response_model=ChartResponse, status_code=201)
async def generate_chart(
    body: ChartGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChartResponse:
    df = await _load_df(body.dataset_id, current_user.id, db)
    df = _apply_aggregation(df, body.x_column, body.y_column, body.aggregation, body.color_column)
    fig = _build_figure(df, body)
    plotly_json = fig.to_dict()

    chart = Chart(
        user_id=current_user.id,
        dashboard_id=body.dashboard_id,
        dataset_id=body.dataset_id,
        title=body.title or f"{body.y_column} by {body.x_column}",
        chart_type=body.chart_type,
        config={
            "x_column": body.x_column,
            "y_column": body.y_column,
            "aggregation": body.aggregation,
            "color_column": body.color_column,
        },
        plotly_json=plotly_json,
    )
    db.add(chart)
    await db.flush()
    return ChartResponse.model_validate(chart)


@router.get("/{chart_id}", response_model=ChartResponse)
async def get_chart(
    chart_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChartResponse:
    result = await db.execute(select(Chart).where(Chart.id == chart_id, Chart.user_id == current_user.id))
    chart = result.scalar_one_or_none()
    if chart is None:
        raise HTTPException(status_code=404, detail="Chart not found")
    return ChartResponse.model_validate(chart)


@router.get("/{chart_id}/image")
async def get_chart_image(
    chart_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    result = await db.execute(select(Chart).where(Chart.id == chart_id, Chart.user_id == current_user.id))
    chart = result.scalar_one_or_none()
    if chart is None:
        raise HTTPException(status_code=404, detail="Chart not found")

    try:
        import plotly.io as pio
        fig = go.Figure(chart.plotly_json)
        img_bytes = pio.to_image(fig, format="png", width=900, height=500)
        return Response(content=img_bytes, media_type="image/png")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {exc}") from exc
