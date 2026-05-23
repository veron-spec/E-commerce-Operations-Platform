"""Celery tasks for data synchronization."""

from asyncio import run

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sync.orchestrator import SyncOrchestrator
from app.infrastructure.celery_app import celery_app
from app.infrastructure.database import async_session
from app.models.store import Store


async def _sync_store(store_id: int):
    async with async_session() as db:
        orchestrator = SyncOrchestrator(db)
        results = await orchestrator.sync_store(store_id)
        logger.info(f"Sync completed for store {store_id}: {results}")
        return results


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_store(self, store_id: int):
    """Synchronize all data for a single store."""
    try:
        return run(_sync_store(store_id))
    except Exception as exc:
        logger.error(f"Sync failed for store {store_id}: {exc}")
        raise self.retry(exc=exc)


async def _sync_all_stores():
    async with async_session() as db:
        result = await db.execute(select(Store).where(Store.is_active == True))
        stores = result.scalars().all()

    results = []
    for store in stores:
        try:
            res = await _sync_store(store.id)
            results.append({"store_id": store.id, "status": "ok", "details": res})
        except Exception as e:
            logger.error(f"Sync failed for store {store.id}: {e}")
            results.append({"store_id": store.id, "status": "error", "error": str(e)})
    return results


@celery_app.task
def sync_all_stores():
    """Synchronize all active stores."""
    return run(_sync_all_stores())
