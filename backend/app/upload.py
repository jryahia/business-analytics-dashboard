from __future__ import annotations

import io
import os
import uuid
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Dataset, DatasetRow, User

router = APIRouter(prefix="/api/datasets", tags=["datasets"])
CHUNK_SIZE = 1000  # rows per insert batch


def _infer_column_types(df: pd.DataFrame) -> dict[str, str]:
    type_map: dict[str, str] = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if "int" in dtype:
            type_map[col] = "integer"
        elif "float" in dtype:
            type_map[col] = "float"
        elif "datetime" in dtype:
            type_map[col] = "datetime"
        elif "bool" in dtype:
            type_map[col] = "boolean"
        else:
            type_map[col] = "string"
    return type_map


def _sanitize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert non-JSON-serializable types to primitives."""
    result: dict[str, Any] = {}
    for k, v in row.items():
        if pd.isna(v) if not isinstance(v, (list, dict)) else False:
            result[k] = None
        elif hasattr(v, "item"):
            result[k] = v.item()
        elif hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    try:
        df = pd.read_csv(io.BytesIO(content), low_memory=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    # Attempt datetime parsing on object columns
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
        except Exception:
            pass

    dataset_name = os.path.splitext(file.filename)[0]
    table_name = f"ds_{uuid.uuid4().hex[:12]}"
    column_info = _infer_column_types(df)

    dataset = Dataset(
        user_id=current_user.id,
        name=dataset_name,
        source_type="csv",
        table_name=table_name,
        columns={"columns": column_info, "names": list(df.columns)},
        row_count=len(df),
        status="ready",
    )
    db.add(dataset)
    await db.flush()

    # Insert rows in chunks
    records = df.to_dict(orient="records")
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i : i + CHUNK_SIZE]
        db.add_all([DatasetRow(dataset_id=dataset.id, data=_sanitize_row(r)) for r in chunk])
        await db.flush()

    return {"id": dataset.id, "name": dataset.name, "row_count": dataset.row_count, "columns": column_info}
