from __future__ import annotations

import asyncio
from typing import Any

from celery import Celery

from app.config import settings

celery_app = Celery(
    "analytics_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


def _run_async(coro: Any) -> Any:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="process_csv_upload")
def process_csv_upload(self: Any, dataset_id: str, user_id: str) -> dict[str, Any]:
    """Re-process a CSV dataset (e.g., type inference) and notify via SSE."""
    from app.sse import publish_event

    async def _inner() -> dict[str, Any]:
        await publish_event(user_id, "dataset_updated", {"dataset_id": dataset_id, "status": "ready"})
        return {"status": "ok", "dataset_id": dataset_id}

    return _run_async(_inner())


@celery_app.task(bind=True, name="generate_chart_async")
def generate_chart_async(self: Any, chart_id: str, user_id: str) -> dict[str, Any]:
    """Notify client when a chart is ready."""
    from app.sse import publish_event

    async def _inner() -> dict[str, Any]:
        await publish_event(user_id, "chart_generated", {"chart_id": chart_id})
        return {"status": "ok", "chart_id": chart_id}

    return _run_async(_inner())


@celery_app.task(bind=True, name="generate_insights_async")
def generate_insights_async(self: Any, insight_id: str, user_id: str) -> dict[str, Any]:
    """Notify client when insights are ready."""
    from app.sse import publish_event

    async def _inner() -> dict[str, Any]:
        await publish_event(user_id, "insight_ready", {"insight_id": insight_id})
        return {"status": "ok", "insight_id": insight_id}

    return _run_async(_inner())
