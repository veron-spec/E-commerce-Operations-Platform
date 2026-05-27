from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adapters.factory import adapter_factory
from app.core.sync.orders import OrderSyncService
from app.core.sync.products import ProductSyncService
from app.core.sync.customers import CustomerSyncService
from app.models.store import Store
from app.models.sync_job import SyncJob


class SyncOrchestrator:
    """Coordinates data synchronization across all entity types for a store."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _last_sync_time(self, store_id: int) -> datetime | None:
        """Find the last successful sync time for incremental sync."""
        result = await self.db.execute(
            select(SyncJob.completed_at)
            .where(SyncJob.store_id == store_id, SyncJob.status == "completed")
            .order_by(SyncJob.completed_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row if row else None

    async def sync_store(self, store_id: int) -> dict:
        result = await self.db.execute(select(Store).where(Store.id == store_id))
        store = result.scalar_one_or_none()
        if not store:
            raise ValueError(f"Store {store_id} not found")
        if not store.is_active:
            return {"status": "skipped", "reason": "Store is inactive"}

        adapter = adapter_factory(
            platform_type=store.platform_type,
            api_key=store.api_key,
            api_secret=store.api_secret,
            store_url=store.store_url,
        )

        last_sync = await self._last_sync_time(store_id)
        results = {}

        # Sync products first (needed for order line-item references)
        product_service = ProductSyncService(self.db, adapter)
        results["products"] = await product_service.sync(store_id, updated_since=last_sync)

        # Sync orders
        order_service = OrderSyncService(self.db, adapter)
        results["orders"] = await order_service.sync(store_id, updated_since=last_sync)

        # Sync customers
        customer_service = CustomerSyncService(self.db, adapter)
        results["customers"] = await customer_service.sync(store_id)

        return results

    async def _log_job(
        self, store_id: int, sync_type: str, status: str,
        processed: int = 0, failed: int = 0, errors: list | None = None
    ) -> SyncJob:
        job = SyncJob(
            store_id=store_id,
            sync_type=sync_type,
            status=status,
            records_processed=processed,
            records_failed=failed,
            error_log=errors or [],
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC) if status in ("completed", "failed") else None,
        )
        self.db.add(job)
        await self.db.commit()
        return job
