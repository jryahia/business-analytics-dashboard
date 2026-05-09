from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, field_validator


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dataset ─────────────────────────────────────────────────────────────────

class DatasetResponse(BaseModel):
    id: str
    name: str
    source_type: str
    table_name: str
    columns: dict[str, Any]
    row_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total: int


class ConnectDatasetRequest(BaseModel):
    name: str
    datasource_id: str
    query: str = "SELECT * FROM {table} LIMIT 10000"
    table_name: str = ""


# ─── DataSource ──────────────────────────────────────────────────────────────

class DataSourceCreateRequest(BaseModel):
    name: str
    source_type: str  # postgresql | mysql | sqlite
    host: str = ""
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    filepath: str = ""  # for sqlite


class DataSourceResponse(BaseModel):
    id: str
    name: str
    source_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Analytics ───────────────────────────────────────────────────────────────

class AggregateRequest(BaseModel):
    dataset_id: str
    group_by: list[str]
    aggregations: dict[str, str]  # {column: "sum"|"mean"|"count"|"min"|"max"}
    filters: dict[str, Any] = {}


class PivotRequest(BaseModel):
    dataset_id: str
    index: str
    columns: str
    values: str
    aggfunc: str = "sum"


class TimeSeriesRequest(BaseModel):
    dataset_id: str
    date_column: str
    value_column: str
    frequency: str = "D"  # D=daily, W=weekly, M=monthly
    aggregation: str = "sum"


class CustomAnalyticsRequest(BaseModel):
    dataset_id: str
    expression: str  # pandas expression like "df.groupby('col').agg({'val': 'sum'})"


class AnalyticsResult(BaseModel):
    data: list[dict[str, Any]]
    columns: list[str]
    metadata: dict[str, Any] = {}


# ─── Charts ──────────────────────────────────────────────────────────────────

class ChartGenerateRequest(BaseModel):
    dataset_id: str
    chart_type: str  # bar | line | pie | scatter | area | heatmap
    x_column: str
    y_column: str
    title: str = ""
    color_column: str | None = None
    aggregation: str | None = None  # sum | mean | count | none
    dashboard_id: str | None = None


class ChartResponse(BaseModel):
    id: str
    title: str
    chart_type: str
    dataset_id: str
    dashboard_id: str | None
    config: dict[str, Any]
    plotly_json: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardCreateRequest(BaseModel):
    name: str
    description: str = ""
    layout: dict[str, Any] = {}


class DashboardUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    layout: dict[str, Any] | None = None


class DashboardResponse(BaseModel):
    id: str
    name: str
    description: str
    layout: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    charts: list[ChartResponse] = []

    class Config:
        from_attributes = True


# ─── Insights ─────────────────────────────────────────────────────────────────

class InsightGenerateRequest(BaseModel):
    dataset_id: str | None = None
    dashboard_id: str | None = None
    regenerate: bool = False


class InsightResponse(BaseModel):
    id: str
    dataset_id: str
    content: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── SSE ─────────────────────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    event: str
    data: dict[str, Any]
