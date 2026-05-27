from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adapters.base import PlatformAdapter
from app.models.customer import Customer


class CustomerSyncService:
    def __init__(self, db: AsyncSession, adapter: PlatformAdapter):
        self.db = db
        self.adapter = adapter

    async def sync(self, store_id: int) -> dict:
        unified_customers = await self.adapter.get_customers()

        processed = 0
        failed = 0

        for unified in unified_customers:
            try:
                stmt = select(Customer).where(
                    Customer.store_id == store_id,
                    Customer.platform_id == unified.platform_id,
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    existing.email = unified.email
                    existing.first_name = unified.first_name
                    existing.last_name = unified.last_name
                    existing.orders_count = unified.orders_count
                    existing.total_spent = unified.total_spent
                    existing.is_verified_email = unified.is_verified_email
                else:
                    customer = Customer(
                        store_id=store_id,
                        platform_id=unified.platform_id,
                        email=unified.email,
                        first_name=unified.first_name,
                        last_name=unified.last_name,
                        orders_count=unified.orders_count,
                        total_spent=unified.total_spent,
                        is_verified_email=unified.is_verified_email,
                        created_at=unified.created_at or datetime.now(UTC),
                    )
                    self.db.add(customer)

                processed += 1
            except Exception:
                failed += 1

        await self.db.commit()
        return {"type": "customer", "processed": processed, "failed": failed}
