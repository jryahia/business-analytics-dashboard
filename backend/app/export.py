from __future__ import annotations

import io
import tempfile
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Chart, Dashboard, Dataset, DatasetRow, User

router = APIRouter(prefix="/api/export", tags=["export"])


async def _get_dataset_df(dataset_id: str, user_id: str, db: AsyncSession) -> tuple[pd.DataFrame, str]:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    rows_result = await db.execute(select(DatasetRow.data).where(DatasetRow.dataset_id == dataset_id))
    rows = [r[0] for r in rows_result.all()]
    return pd.DataFrame(rows), dataset.name


@router.get("/dataset/{dataset_id}/csv")
async def export_dataset_csv(
    dataset_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    df, name = await _get_dataset_df(dataset_id, current_user.id, db)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    filename = f"{name}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/dataset/{dataset_id}/excel")
async def export_dataset_excel(
    dataset_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    df, name = await _get_dataset_df(dataset_id, current_user.id, db)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    buf.seek(0)
    filename = f"{name}.xlsx"
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/dashboard/{dashboard_id}/pdf")
async def export_dashboard_pdf(
    dashboard_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.charts))
        .where(Dashboard.id == dashboard_id, Dashboard.user_id == current_user.id)
    )
    dashboard = result.scalar_one_or_none()
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    charts_html = ""
    for chart in dashboard.charts:
        charts_html += f"""
        <div class="chart-container">
            <h3 style="color: #94a3b8; margin: 0 0 8px 0;">{chart.title}</h3>
            <p style="color: #64748b; font-size: 12px; margin: 0;">Chart type: {chart.chart_type}</p>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ background: #0f172a; color: #e2e8f0; font-family: Inter, sans-serif; margin: 0; padding: 24px; }}
        h1 {{ color: #f1f5f9; font-size: 24px; margin-bottom: 8px; }}
        .subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 32px; }}
        .chart-container {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px;
                            padding: 16px; margin-bottom: 16px; }}
        .meta {{ color: #64748b; font-size: 11px; margin-top: 40px; border-top: 1px solid #334155; padding-top: 16px; }}
    </style>
</head>
<body>
    <h1>{dashboard.name}</h1>
    <div class="subtitle">{dashboard.description or "Business Analytics Dashboard"}</div>
    <div class="charts">{charts_html}</div>
    <div class="meta">Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
</body>
</html>"""

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    filename = f"{dashboard.name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
