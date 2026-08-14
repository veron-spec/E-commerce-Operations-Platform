"""QStash task publisher for Vercel Functions."""
from __future__ import annotations

from urllib.parse import quote

import httpx

from app.config import settings


class TaskDispatchError(RuntimeError):
    pass


def _task_url(path: str) -> str:
    base_url = settings.app_base_url.rstrip("/")
    root_path = settings.root_path.rstrip("/")
    if not base_url:
        raise TaskDispatchError("APP_BASE_URL is required to dispatch background tasks")
    return f"{base_url}{root_path}{path}"


async def dispatch_sync_store(store_id: int) -> str:
    if not settings.qstash_token:
        raise TaskDispatchError("QSTASH_TOKEN is required to dispatch background tasks")

    destination = _task_url("/internal/tasks/sync-store")
    publish_url = f"{settings.qstash_url.rstrip('/')}/v2/publish/{quote(destination, safe='')}"
    headers = {
        "Authorization": f"Bearer {settings.qstash_token}",
        "Content-Type": "application/json",
        "Upstash-Retries": "3",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(publish_url, headers=headers, json={"store_id": store_id})
        response.raise_for_status()
    payload = response.json()
    message_id = payload.get("messageId") or payload.get("message_id")
    if not message_id:
        raise TaskDispatchError("QStash did not return a message ID")
    return str(message_id)
