from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adapters.base import PlatformAdapter
from app.models.order import Order


class OrderSyncService:
    def __init__(self, db: AsyncSession, adapter: PlatformAdapter):
        self.db = db
        self.adapter = adapter

    async def sync(self, store_id: int, days_back: int = 30) -> dict:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Fetch unified orders from adapter
        unified_orders = await self.adapter.get_orders(start_date, end_date)

        processed = 0
        failed = 0

        for unified in unified_orders:
            try:
                # Check if order already exists
                stmt = select(Order).where(
                    Order.store_id == store_id,
                    Order.platform_id == unified.platform_id,
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.order_number = unified.order_number
                    existing.email = unified.email
                    existing.line_items = unified.line_items
                    existing.total_price = unified.total_price
                    existing.subtotal_price = unified.subtotal_price
                    existing.total_discount = unified.total_discount
                    existing.shipping_info = unified.shipping_info
                    existing.financial_status = unified.financial_status
                    existing.fulfillment_status = unified.fulfillment_status
                else:
                    # Create new
                    order = Order(
                        store_id=store_id,
                        platform_id=unified.platform_id,
                        order_number=unified.order_number,
                        customer_platform_id=unified.customer_platform_id,
                        email=unified.email,
                        line_items=unified.line_items,
                        total_price=unified.total_price,
                        subtotal_price=unified.subtotal_price,
                        total_discount=unified.total_discount,
                        shipping_info=unified.shipping_info,
                        financial_status=unified.financial_status,
                        fulfillment_status=unified.fulfillment_status,
                        created_at=unified.created_at or datetime.utcnow(),
                    )
                    self.db.add(order)

                processed += 1
            except Exception:
                failed += 1

        await self.db.commit()
        return {"type": "order", "processed": processed, "failed": failed}
