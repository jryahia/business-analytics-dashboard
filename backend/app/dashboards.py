from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Chart, Dashboard, User
from app.schemas import (
    DashboardCreateRequest,
    DashboardResponse,
    DashboardUpdateRequest,
)

router = APIRouter(prefix="/api/dashboards", tags=["dashboards"])


def _to_response(dashboard: Dashboard) -> DashboardResponse:
    from app.schemas import ChartResponse
    charts = [ChartResponse.model_validate(c) for c in (dashboard.charts or [])]
    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        layout=dashboard.layout,
        created_at=dashboard.created_at,
        updated_at=dashboard.updated_at,
        charts=charts,
    )


@router.post("", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    body: DashboardCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardResponse:
    dashboard = Dashboard(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        layout=body.layout,
    )
    db.add(dashboard)
    await db.flush()
    await db.refresh(dashboard, ["charts"])
    return _to_response(dashboard)


@router.get("", response_model=list[DashboardResponse])
async def list_dashboards(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DashboardResponse]:
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.charts))
        .where(Dashboard.user_id == current_user.id)
        .order_by(Dashboard.created_at.desc())
    )
    dashboards = result.scalars().all()
    return [_to_response(d) for d in dashboards]


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardResponse:
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.charts))
        .where(Dashboard.id == dashboard_id, Dashboard.user_id == current_user.id)
    )
    dashboard = result.scalar_one_or_none()
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return _to_response(dashboard)


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    body: DashboardUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardResponse:
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.charts))
        .where(Dashboard.id == dashboard_id, Dashboard.user_id == current_user.id)
    )
    dashboard = result.scalar_one_or_none()
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    if body.name is not None:
        dashboard.name = body.name
    if body.description is not None:
        dashboard.description = body.description
    if body.layout is not None:
        dashboard.layout = body.layout

    await db.flush()
    return _to_response(dashboard)


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id, Dashboard.user_id == current_user.id))
    dashboard = result.scalar_one_or_none()
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    await db.delete(dashboard)


@router.post("/{dashboard_id}/duplicate", response_model=DashboardResponse, status_code=201)
async def duplicate_dashboard(
    dashboard_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardResponse:
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.charts))
        .where(Dashboard.id == dashboard_id, Dashboard.user_id == current_user.id)
    )
    original = result.scalar_one_or_none()
    if original is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    clone = Dashboard(
        user_id=current_user.id,
        name=f"{original.name} (copy)",
        description=original.description,
        layout=original.layout,
    )
    db.add(clone)
    await db.flush()

    for chart in original.charts:
        clone_chart = Chart(
            user_id=current_user.id,
            dashboard_id=clone.id,
            dataset_id=chart.dataset_id,
            title=chart.title,
            chart_type=chart.chart_type,
            config=chart.config,
            plotly_json=chart.plotly_json,
        )
        db.add(clone_chart)

    await db.flush()
    await db.refresh(clone, ["charts"])
    return _to_response(clone)
