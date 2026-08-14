"""Legacy Celery wrappers around synchronization services."""
from __future__ import annotations

import asyncio

from app.infrastructure.celery_app import celery_app
from app.services.sync import sync_all_stores as run_sync_all_stores
from app.services.sync import sync_store as run_sync_store


def _sync_store(store_id: int):
    return asyncio.run(run_sync_store(store_id))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_store(self, store_id: int):
    """Synchronize a single store in local Docker deployments."""
    try:
        return _sync_store(store_id)
    except Exception as exc:
        raise self.retry(exc=exc)


def _sync_all_stores():
    return asyncio.run(run_sync_all_stores())


@celery_app.task
def sync_all_stores():
    """Synchronize every active store in local Docker deployments."""
    return _sync_all_stores()
