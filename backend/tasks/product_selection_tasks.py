"""Celery tasks for product selection scanning."""
from asyncio import run

from loguru import logger

from app.core.product_selection.service import ProductSelectionService
from app.infrastructure.celery_app import celery_app
from app.infrastructure.database import async_session


async def _scan(store_id: int):
    async with async_session() as db:
        service = ProductSelectionService(db)
        return await service.scan_for_winners(store_id)


@celery_app.task
def scan_product_selections(store_id: int = 1):
    try:
        results = run(_scan(store_id))
        logger.info(f"Product selection scan done: {len(results)} candidates")
        return {"found": len(results)}
    except Exception as e:
        logger.error(f"Product selection scan failed: {e}")
        raise
