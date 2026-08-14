"""Store synchronization service independent from the task transport."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session
from app.models.store import Store

try:
    from app.pro.sync.orchestrator import SyncOrchestrator
except ImportError:
    SyncOrchestrator = None


async def sync_store(store_id: int) -> dict:
    async with async_session() as db:
        return await sync_store_with_session(store_id, db)


async def sync_store_with_session(store_id: int, db: AsyncSession) -> dict:
    if SyncOrchestrator is not None:
        return await SyncOrchestrator(db).sync_store(store_id)

    store = await db.scalar(select(Store).where(Store.id == store_id))
    if store is None:
        return {"status": "error", "error": "Store not found"}
    return {"status": "ok", "store_id": store.id}


async def sync_all_stores() -> list[dict]:
    async with async_session() as db:
        store_ids = list((await db.scalars(select(Store.id).where(Store.is_active == True))).all())

    return [await sync_store(store_id) for store_id in store_ids]
