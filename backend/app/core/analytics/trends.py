from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics.metrics import TrendMetrics
from app.models.order import Order


class TrendAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(self, days: int = 60, store_id: int | None = None) -> TrendMetrics:
        metrics = TrendMetrics()
        now = datetime.now(UTC)
        current_start = now - timedelta(days=days // 2)
        previous_start = now - timedelta(days=days)
        mid_point = now - timedelta(days=days // 2)

        # Current period revenue & orders
        cur_stmt = select(
            func.coalesce(func.sum(Order.total_price), 0),
            func.count(Order.id),
        ).where(
            Order.created_at >= current_start,
            Order.created_at <= now,
        )
        if store_id:
            cur_stmt = cur_stmt.where(Order.store_id == store_id)
        cur_result = await self.db.execute(cur_stmt)
        cur_row = cur_result.one()
        metrics.current_period_revenue = float(cur_row[0])
        metrics.current_period_orders = cur_row[1]

        # Previous period (for comparison / growth calculation)
        prev_stmt = select(
            func.coalesce(func.sum(Order.total_price), 0),
            func.count(Order.id),
        ).where(
            Order.created_at >= previous_start,
            Order.created_at < mid_point,
        )
        if store_id:
            prev_stmt = prev_stmt.where(Order.store_id == store_id)
        prev_result = await self.db.execute(prev_stmt)
        prev_row = prev_result.one()
        metrics.previous_period_revenue = float(prev_row[0])
        metrics.previous_period_orders = prev_row[1]

        # Growth percentages
        metrics.revenue_growth_pct = round(
            ((metrics.current_period_revenue - metrics.previous_period_revenue)
             / metrics.previous_period_revenue * 100) if metrics.previous_period_revenue else 0, 2
        )
        metrics.order_growth_pct = round(
            ((metrics.current_period_orders - metrics.previous_period_orders)
             / metrics.previous_period_orders * 100) if metrics.previous_period_orders else 0, 2
        )

        # Daily revenue for trend chart
        stmt = (
            select(
                func.date(Order.created_at).label("day"),
                func.coalesce(func.sum(Order.total_price), 0).label("revenue"),
            )
            .where(Order.created_at >= previous_start)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        if store_id:
            stmt = stmt.where(Order.store_id == store_id)

        result = await self.db.execute(stmt)
        for row in result.all():
            day_val = row.day.isoformat() if hasattr(row.day, 'isoformat') else str(row.day)
            metrics.daily_revenue.append({
                "date": day_val,
                "revenue": float(row.revenue),
            })

        return metrics
