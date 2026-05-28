"""Celery tasks for report generation."""

from asyncio import run

from loguru import logger

from app.infrastructure.celery_app import celery_app
from app.infrastructure.database import async_session

try:
    from app.pro.analytics.reports import ReportGenerator
except ImportError:
    ReportGenerator = None


async def _generate_and_cache_report(store_id: int, report_type: str, days: int = 30):
    async with async_session() as db:
        gen = ReportGenerator(db)
        if report_type == "sales":
            csv_data = await gen.generate_sales_csv(days=days, store_id=store_id)
        elif report_type == "inventory":
            csv_data = await gen.generate_inventory_csv(store_id=store_id)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        return csv_data


@celery_app.task
def generate_report(store_id: int, report_type: str, days: int = 30):
    """Generate and cache a report asynchronously."""
    try:
        data = run(_generate_and_cache_report(store_id, report_type, days))
        logger.info(f"Report generated for store {store_id}: {report_type}")
        return data
    except Exception as e:
        logger.error(f"Report generation failed for store {store_id}: {e}")
        raise
