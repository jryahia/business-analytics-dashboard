from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Business Analytics Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Register routers
from app.auth import router as auth_router
from app.upload import router as upload_router
from app.datasets import router as datasets_router
from app.datasources import router as datasources_router
from app.analytics import router as analytics_router
from app.charts import router as charts_router
from app.dashboards import router as dashboards_router
from app.insights import router as insights_router
from app.export import router as export_router
from app.sse import router as sse_router

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(datasets_router)
app.include_router(datasources_router)
app.include_router(analytics_router)
app.include_router(charts_router)
app.include_router(dashboards_router)
app.include_router(insights_router)
app.include_router(export_router)
app.include_router(sse_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}
