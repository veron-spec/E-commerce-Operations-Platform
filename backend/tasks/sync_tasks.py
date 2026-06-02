"""Celery tasks for data synchronization."""
import asyncio

from loguru import logger
from sqlalchemy import select

from app.infrastructure.celery_app import celery_app
from app.infrastructure.database import async_session, sync_session
from app.models.store import Store

try:
    from app.pro.sync.orchestrator import SyncOrchestrator
except ImportError:
    SyncOrchestrator = None


def _sync_store(store_id: int):
    """Sync a single store — uses async orchestrator when Pro module is installed."""
    if SyncOrchestrator is not None:
        async def _run():
            async with async_session() as db:
                orchestrator = SyncOrchestrator(db)
                return await orchestrator.sync_store(store_id)
        return asyncio.run(_run())

    # Community edition: lightweight fallback
    with sync_session() as db:
        result = db.execute(select(Store).where(Store.id == store_id))
        store = result.scalar_one_or_none()
        if not store:
            logger.warning(f"Store {store_id} not found")
            return {"status": "error", "error": "Store not found"}
        logger.info(f"Sync completed for store {store_id}")
        return {"status": "ok"}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_store(self, store_id: int):
    """Synchronize all data for a single store."""
    try:
        return _sync_store(store_id)
    except Exception as exc:
        logger.error(f"Sync failed for store {store_id}: {exc}")
        raise self.retry(exc=exc)


def _sync_all_stores():
    with sync_session() as db:
        result = db.execute(select(Store).where(Store.is_active == True))
        stores = result.scalars().all()

    results = []
    for store in stores:
        try:
            res = _sync_store(store.id)
            results.append({"store_id": store.id, "status": "ok", "details": res})
        except Exception as e:
            logger.error(f"Sync failed for store {store.id}: {e}")
            results.append({"store_id": store.id, "status": "error", "error": str(e)})
    return results


@celery_app.task
def sync_all_stores():
    """Synchronize all active stores."""
    return _sync_all_stores()
