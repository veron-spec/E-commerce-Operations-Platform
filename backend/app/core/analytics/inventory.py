from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics.metrics import InventoryMetrics
from app.models.product import Product


class InventoryAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self, store_id: int | None = None, low_stock_threshold: int = 10
    ) -> InventoryMetrics:
        metrics = InventoryMetrics()

        # Base query
        stmt = select(Product)
        count_stmt = select(func.count(Product.id))
        if store_id:
            stmt = stmt.where(Product.store_id == store_id)
            count_stmt = count_stmt.where(Product.store_id == store_id)

        # Total products
        total = await self.db.execute(count_stmt)
        metrics.total_products = total.scalar() or 0

        # All products for analysis
        result = await self.db.execute(stmt)
        products = result.scalars().all()

        metrics.total_stock_quantity = sum(p.inventory_quantity for p in products)

        # Low stock / out of stock / overstock
        for p in products:
            if p.inventory_quantity <= 0:
                metrics.out_of_stock_count += 1
            elif p.inventory_quantity < low_stock_threshold:
                metrics.low_stock_count += 1
            elif p.inventory_quantity > low_stock_threshold * 10:
                metrics.overstock_count += 1

            if p.inventory_quantity < low_stock_threshold:
                metrics.low_stock_items.append({
                    "id": p.id,
                    "title": p.title,
                    "sku": p.sku,
                    "quantity": p.inventory_quantity,
                })

        # Category distribution
        cat_stmt = (
            select(Product.category, func.count(Product.id).label("count"))
            .where(Product.category.isnot(None))
            .group_by(Product.category)
        )
        if store_id:
            cat_stmt = cat_stmt.where(Product.store_id == store_id)
        cat_result = await self.db.execute(cat_stmt)
        for row in cat_result.all():
            metrics.category_distribution.append({
                "category": row.category,
                "count": row.count,
            })

        return metrics
