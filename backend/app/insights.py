from __future__ import annotations

import json
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Dataset, DatasetRow, Insight, User
from app.schemas import InsightGenerateRequest, InsightResponse

router = APIRouter(prefix="/api/insights", tags=["insights"])


def _summarize_df(df: pd.DataFrame) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "rows": len(df),
        "columns": list(df.columns),
        "numeric_stats": {},
        "categorical_preview": {},
    }
    for col in df.select_dtypes(include=["number"]).columns:
        summary["numeric_stats"][col] = {
            "mean": round(float(df[col].mean()), 4) if not df[col].isna().all() else None,
            "min": float(df[col].min()) if not df[col].isna().all() else None,
            "max": float(df[col].max()) if not df[col].isna().all() else None,
            "std": round(float(df[col].std()), 4) if not df[col].isna().all() else None,
        }
    for col in df.select_dtypes(include=["object"]).columns[:5]:
        vc = df[col].value_counts().head(5).to_dict()
        summary["categorical_preview"][col] = {str(k): int(v) for k, v in vc.items()}
    return summary


async def _generate_openai_insights(summary: dict[str, Any], dataset_name: str) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        return _fallback_insights(summary, dataset_name)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = f"""You are a business intelligence analyst. Analyze this dataset summary and generate actionable business insights.

Dataset: {dataset_name}
Summary: {json.dumps(summary, indent=2)}

Generate:
1. Three concise business insights (each 1-2 sentences)
2. One executive summary (2-3 sentences)
3. Two recommended actions based on the data

Respond with valid JSON:
{{
  "insights": ["insight 1", "insight 2", "insight 3"],
  "summary": "executive summary",
  "recommendations": ["action 1", "action 2"]
}}"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        return json.loads(response.choices[0].message.content or "{}")
    except Exception:
        return _fallback_insights(summary, dataset_name)


def _fallback_insights(summary: dict[str, Any], dataset_name: str) -> dict[str, Any]:
    insights: list[str] = []
    rows = summary.get("rows", 0)
    cols = summary.get("columns", [])
    numeric_stats = summary.get("numeric_stats", {})

    insights.append(f"The dataset '{dataset_name}' contains {rows:,} records across {len(cols)} dimensions.")

    if numeric_stats:
        top_col = list(numeric_stats.keys())[0]
        stats = numeric_stats[top_col]
        if stats.get("mean") is not None:
            insights.append(
                f"'{top_col}' averages {stats['mean']:,.2f} with values ranging from {stats['min']:,.2f} to {stats['max']:,.2f}."
            )

    cat_preview = summary.get("categorical_preview", {})
    if cat_preview:
        col = list(cat_preview.keys())[0]
        top_val = list(cat_preview[col].keys())[0] if cat_preview[col] else ""
        if top_val:
            insights.append(f"The most common value in '{col}' is '{top_val}', suggesting it may be a key segment.")

    while len(insights) < 3:
        insights.append("Explore the data further by applying filters and aggregations to uncover hidden trends.")

    return {
        "insights": insights[:3],
        "summary": f"Dataset '{dataset_name}' with {rows:,} rows and {len(cols)} columns. Key numeric metrics available for analysis.",
        "recommendations": [
            "Apply time-series analysis if a date column is present to identify trends.",
            "Segment by categorical columns to find performance differences across groups.",
        ],
    }


@router.post("/generate", response_model=InsightResponse, status_code=201)
async def generate_insights(
    body: InsightGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsightResponse:
    dataset_id = body.dataset_id
    if not dataset_id and body.dashboard_id:
        raise HTTPException(status_code=400, detail="Provide dataset_id or dataset_id derived from dashboard")
    if not dataset_id:
        raise HTTPException(status_code=400, detail="dataset_id is required")

    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not body.regenerate:
        existing = await db.execute(
            select(Insight).where(Insight.dataset_id == dataset_id, Insight.user_id == current_user.id)
            .order_by(Insight.created_at.desc())
        )
        prev = existing.scalar_one_or_none()
        if prev:
            return InsightResponse.model_validate(prev)

    rows_result = await db.execute(select(DatasetRow.data).where(DatasetRow.dataset_id == dataset_id).limit(5000))
    rows = [r[0] for r in rows_result.all()]
    df = pd.DataFrame(rows)

    summary = _summarize_df(df)
    content = await _generate_openai_insights(summary, dataset.name)

    insight = Insight(
        user_id=current_user.id,
        dataset_id=dataset_id,
        content=content,
    )
    db.add(insight)
    await db.flush()
    return InsightResponse.model_validate(insight)


@router.get("/{dataset_id}", response_model=InsightResponse)
async def get_insight(
    dataset_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsightResponse:
    result = await db.execute(
        select(Insight)
        .where(Insight.dataset_id == dataset_id, Insight.user_id == current_user.id)
        .order_by(Insight.created_at.desc())
    )
    insight = result.scalar_one_or_none()
    if insight is None:
        raise HTTPException(status_code=404, detail="No insights found for this dataset")
    return InsightResponse.model_validate(insight)
