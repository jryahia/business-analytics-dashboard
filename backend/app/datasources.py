from __future__ import annotations

import base64
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import DataSource, Dataset, DatasetRow, User
from app.schemas import DataSourceCreateRequest, DataSourceResponse

router = APIRouter(prefix="/api/datasources", tags=["datasources"])

CHUNK_SIZE = 1000


def _encrypt(data: str) -> str:
    encoded = data.encode("utf-8")
    return base64.b64encode(encoded).decode("utf-8")


def _decrypt(data: str) -> str:
    decoded = base64.b64decode(data.encode("utf-8"))
    return decoded.decode("utf-8")


def _build_connection_url(config: dict[str, Any]) -> str:
    source_type = config.get("source_type", "")
    if source_type == "postgresql":
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        database = config.get("database", "")
        username = config.get("username", "")
        password = config.get("password", "")
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    elif source_type == "mysql":
        host = config.get("host", "localhost")
        port = config.get("port", 3306)
        database = config.get("database", "")
        username = config.get("username", "")
        password = config.get("password", "")
        return f"mysql+aiomysql://{username}:{password}@{host}:{port}/{database}"
    elif source_type == "sqlite":
        filepath = config.get("filepath", "database.db")
        return f"sqlite+aiosqlite:///{filepath}"
    raise HTTPException(status_code=400, detail=f"Unsupported source type: {source_type}")


@router.post("", response_model=DataSourceResponse, status_code=201)
async def create_datasource(
    body: DataSourceCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataSourceResponse:
    config_data = {
        "source_type": body.source_type,
        "host": body.host,
        "port": body.port,
        "database": body.database,
        "username": body.username,
        "password": body.password,
        "filepath": body.filepath,
    }
    encrypted = _encrypt(json.dumps(config_data))

    datasource = DataSource(
        user_id=current_user.id,
        name=body.name,
        source_type=body.source_type,
        config_encrypted=encrypted,
    )
    db.add(datasource)
    await db.flush()
    return DataSourceResponse.model_validate(datasource)


@router.get("", response_model=list[DataSourceResponse])
async def list_datasources(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DataSourceResponse]:
    result = await db.execute(
        select(DataSource).where(DataSource.user_id == current_user.id).order_by(DataSource.created_at.desc())
    )
    sources = result.scalars().all()
    return [DataSourceResponse.model_validate(s) for s in sources]


@router.post("/{datasource_id}/sync", status_code=201)
async def sync_datasource(
    datasource_id: str,
    table_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    result = await db.execute(select(DataSource).where(DataSource.id == datasource_id, DataSource.user_id == current_user.id))
    datasource = result.scalar_one_or_none()
    if datasource is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    try:
        config_data = json.loads(_decrypt(datasource.config_encrypted))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to decrypt config") from exc

    conn_url = _build_connection_url(config_data)

    try:
        import pandas as pd
        from sqlalchemy.ext.asyncio import create_async_engine

        ext_engine = create_async_engine(conn_url, echo=False)
        async with ext_engine.connect() as conn:
            result_proxy = await conn.execute(text(f"SELECT * FROM {table_name} LIMIT 50000"))  # noqa: S608
            rows_data = [dict(r._mapping) for r in result_proxy.fetchall()]
            col_names = list(result_proxy.keys())
        await ext_engine.dispose()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to query external source: {exc}") from exc

    if not rows_data:
        raise HTTPException(status_code=400, detail="No data returned from external source")

    df = pd.DataFrame(rows_data)
    column_info: dict[str, str] = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if "int" in dtype:
            column_info[col] = "integer"
        elif "float" in dtype:
            column_info[col] = "float"
        elif "datetime" in dtype or "date" in dtype:
            column_info[col] = "datetime"
        else:
            column_info[col] = "string"

    dataset = Dataset(
        user_id=current_user.id,
        name=f"{datasource.name} — {table_name}",
        source_type="external",
        table_name=table_name,
        columns={"columns": column_info, "names": col_names},
        row_count=len(rows_data),
        status="ready",
    )
    db.add(dataset)
    await db.flush()

    for i in range(0, len(rows_data), CHUNK_SIZE):
        chunk = rows_data[i : i + CHUNK_SIZE]
        sanitized = []
        for row in chunk:
            clean: dict[str, Any] = {}
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    clean[k] = v.isoformat()
                elif v is None:
                    clean[k] = None
                else:
                    clean[k] = v
            sanitized.append(clean)
        db.add_all([DatasetRow(dataset_id=dataset.id, data=r) for r in sanitized])
        await db.flush()

    return {"id": dataset.id, "name": dataset.name, "row_count": dataset.row_count}


@router.delete("/{datasource_id}", status_code=204)
async def delete_datasource(
    datasource_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(DataSource).where(DataSource.id == datasource_id, DataSource.user_id == current_user.id))
    ds = result.scalar_one_or_none()
    if ds is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    await db.delete(ds)
