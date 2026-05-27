from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adapters.base import PlatformAdapter
from app.models.product import Product


class ProductSyncService:
    def __init__(self, db: AsyncSession, adapter: PlatformAdapter):
        self.db = db
        self.adapter = adapter

    async def sync(self, store_id: int, updated_since: datetime | None = None) -> dict:
        unified_products = await self.adapter.get_products(updated_since=updated_since)

        processed = 0
        failed = 0

        for unified in unified_products:
            try:
                stmt = select(Product).where(
                    Product.store_id == store_id,
                    Product.platform_id == unified.platform_id,
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    existing.title = unified.title
                    existing.description = unified.description
                    existing.price = unified.price
                    existing.compare_at_price = unified.compare_at_price
                    existing.sku = unified.sku
                    existing.barcode = unified.barcode
                    existing.category = unified.category
                    existing.tags = unified.tags
                    existing.images = unified.images
                    existing.status = unified.status
                    existing.inventory_quantity = unified.inventory_quantity
                else:
                    product = Product(
                        store_id=store_id,
                        platform_id=unified.platform_id,
                        title=unified.title,
                        description=unified.description,
                        price=unified.price,
                        compare_at_price=unified.compare_at_price,
                        sku=unified.sku,
                        barcode=unified.barcode,
                        category=unified.category,
                        tags=unified.tags,
                        images=unified.images,
                        status=unified.status,
                        inventory_quantity=unified.inventory_quantity,
                        created_at=unified.created_at or datetime.now(UTC),
                    )
                    self.db.add(product)

                processed += 1
            except Exception:
                failed += 1

        await self.db.commit()
        return {"type": "product", "processed": processed, "failed": failed}
