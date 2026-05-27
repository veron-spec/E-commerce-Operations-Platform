"""Analyze orders + products to identify potential winning products."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.product import Product


class ProductSelectionAnalyzer:
    """Scans sales data to compute growth metrics and scores for product selection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_for_winners(self, store_id: int) -> list[dict]:
        """Analyze recent orders and inventory to find high-potential products.

        Scoring formula:
          score = growth_rate * 0.3 + margin * 0.3 + sales_velocity * 0.4
        where:
          - growth_rate: week-over-week sales volume increase (capped at 0-100)
          - margin: estimated profit margin % (capped at 0-100)
          - sales_velocity: units sold per day across recent orders (normalized to 0-100)

        Returns candidates with score >= 60.
        """
        now = datetime.now(UTC)
        recent_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)

        # Get all active products for this store
        product_result = await self.db.execute(
            select(Product).where(
                Product.store_id == store_id,
                Product.status == "active",
            )
        )
        products = product_result.scalars().all()

        if not products:
            return []

        # Aggregate sales volume per product from order line_items for recent and previous periods
        # Uses JSON extraction on line_items to find product quantities
        recent_volumes: dict[int, int] = {}
        previous_volumes: dict[int, int] = {}

        for period_start, period_end, target in [
            (recent_start, now, recent_volumes),
            (previous_start, recent_start, previous_volumes),
        ]:
            order_result = await self.db.execute(
                select(Order).where(
                    Order.store_id == store_id,
                    Order.created_at >= period_start,
                    Order.created_at < period_end,
                    Order.financial_status != "refunded",
                )
            )
            for order in order_result.scalars().all():
                if not order.line_items:
                    continue
                for item in order.line_items:
                    product_id = item.get("product_id")
                    qty = item.get("quantity", 0)
                    # Map by product title since platform_id may differ from local PK
                    # We'll match products by title/sku later
                    title = item.get("title", "")
                    target[id(title)] = target.get(id(title), 0) + qty

        # Match line_items to local products by title
        product_map = {p.title: p for p in products if p.title}

        candidates = []
        for product in products:
            title_key = id(product.title)
            recent_qty = recent_volumes.get(title_key, 0)
            previous_qty = previous_volumes.get(title_key, 0)

            # Growth rate (prevent division by zero)
            if previous_qty > 0:
                growth_rate = max(0, min(100, ((recent_qty - previous_qty) / previous_qty) * 100))
            else:
                growth_rate = 50 if recent_qty > 0 else 0  # new product with sales = moderate

            # Estimate margin from price (simplified)
            margin = min(80, max(5, (product.price - product.price * 0.6) / product.price * 100))

            # Sales velocity (units/day, normalized)
            velocity = min(100, recent_qty * 10)

            # Composite score
            score = growth_rate * 0.3 + margin * 0.3 + velocity * 0.4

            if score >= 60:
                reasons = []
                if growth_rate > 20:
                    reasons.append(f"周增长率 {growth_rate:.0f}%")
                if product.inventory_quantity < 50 and recent_qty > 5:
                    reasons.append("低库存高销量")
                if margin > 40:
                    reasons.append(f"毛利率 {margin:.0f}%")

                candidates.append({
                    "product_id": product.id,
                    "title": product.title,
                    "platform": "taobao",  # default
                    "category": product.category or "",
                    "price": product.price,
                    "sales_volume": recent_qty,
                    "growth_rate": round(growth_rate, 1),
                    "margin": round(margin, 1),
                    "selection_score": round(score, 1),
                    "reason": "；".join(reasons) if reasons else "综合评分达标",
                })

        candidates.sort(key=lambda x: x["selection_score"], reverse=True)
        return candidates
