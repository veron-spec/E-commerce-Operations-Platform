"""QStash-only task endpoints. These routes are never exposed to browsers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.config import settings
from app.services.sync import sync_store

router = APIRouter(prefix="/internal/tasks", include_in_schema=False)


class SyncStoreTask(BaseModel):
    store_id: int


def _verify_qstash(request: Request, body: bytes, path: str) -> None:
    signature = request.headers.get("Upstash-Signature")
    if not signature or not settings.qstash_current_signing_key or not settings.qstash_next_signing_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid task signature")

    from qstash import Receiver

    receiver = Receiver(
        current_signing_key=settings.qstash_current_signing_key,
        next_signing_key=settings.qstash_next_signing_key,
    )
    expected_url = f"{settings.app_base_url.rstrip('/')}{settings.root_path.rstrip('/')}{path}"
    try:
        receiver.verify(body=body, signature=signature, url=expected_url)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid task signature") from exc


@router.post("/sync-store")
async def run_sync_store(task: SyncStoreTask, request: Request):
    _verify_qstash(request, await request.body(), "/internal/tasks/sync-store")
    return await sync_store(task.store_id)
