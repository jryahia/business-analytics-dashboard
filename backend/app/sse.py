from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.config import settings
from app.models import User

router = APIRouter(prefix="/api/events", tags=["sse"])


async def _event_generator(user_id: str) -> AsyncGenerator[str, None]:
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    channel = f"events:{user_id}"
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)

    # Send initial connection event
    yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'user_id': user_id})}\n\n"

    try:
        while True:
            try:
                message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=30.0)
                if message and message["type"] == "message":
                    data = message["data"]
                    try:
                        parsed = json.loads(data)
                        event_type = parsed.get("event", "message")
                        yield f"event: {event_type}\ndata: {json.dumps(parsed.get('data', {}))}\n\n"
                    except json.JSONDecodeError:
                        yield f"event: message\ndata: {json.dumps({'raw': data})}\n\n"
                else:
                    # Heartbeat to keep connection alive
                    yield f"event: heartbeat\ndata: {json.dumps({'ts': asyncio.get_event_loop().time()})}\n\n"
            except asyncio.TimeoutError:
                yield f"event: heartbeat\ndata: {json.dumps({'ts': asyncio.get_event_loop().time()})}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await client.aclose()


@router.get("")
async def sse_stream(
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    return StreamingResponse(
        _event_generator(current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def publish_event(user_id: str, event_type: str, data: dict) -> None:
    """Publish an event to a user's SSE channel via Redis pub/sub."""
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        payload = json.dumps({"event": event_type, "data": data})
        await client.publish(f"events:{user_id}", payload)
        await client.aclose()
    except Exception:
        pass  # SSE is best-effort
