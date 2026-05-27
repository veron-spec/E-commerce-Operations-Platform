from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics.metrics import SalesMetrics
from app.models.order import Order


class SalesAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self, days: int = 30, store_id: int | None = None, granularity: str = "day"
    ) -> SalesMetrics:
        since = datetime.now(UTC) - timedelta(days=days)
        metrics = SalesMetrics()

        # Aggregate by time granularity
        if granularity == "day":
            date_col = func.date(Order.created_at)
        elif granularity == "week":
            date_col = func.date_trunc("week", Order.created_at)
        else:
            date_col = func.date_trunc("month", Order.created_at)

        stmt = (
            select(
                date_col.label("period"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_price), 0).label("revenue"),
                func.coalesce(func.sum(Order.total_discount), 0).label("discounts"),
            )
            .where(Order.created_at >= since)
            .group_by(date_col)
            .order_by(date_col)
        )
        if store_id:
            stmt = stmt.where(Order.store_id == store_id)

        result = await self.db.execute(stmt)
        rows = result.all()

        for row in rows:
            period_str = row.period.isoformat() if hasattr(row.period, 'isoformat') else str(row.period)
            entry = {
                "period": period_str,
                "revenue": float(row.revenue),
                "order_count": row.order_count,
                "discounts": float(row.discounts),
            }
            if granularity == "day":
                metrics.revenue_by_day.append(entry)
            elif granularity == "week":
                metrics.revenue_by_week.append(entry)
            else:
                metrics.revenue_by_month.append(entry)

            metrics.total_revenue += float(row.revenue)
            metrics.order_count += row.order_count
            metrics.total_discount += float(row.discounts)

        metrics.avg_order_value = round(metrics.total_revenue / metrics.order_count, 2) if metrics.order_count else 0.0

        # Calculate refund stats
        refund_stmt = select(
            func.coalesce(func.sum(Order.total_price), 0),
            func.count(Order.id),
        ).where(Order.financial_status == "refunded")
        if store_id:
            refund_stmt = refund_stmt.where(Order.store_id == store_id)
        refund_result = await self.db.execute(refund_stmt)
        refund_row = refund_result.one()
        metrics.refund_amount = float(refund_row[0])
        refund_count = refund_row[1]
        metrics.refund_rate = round(
            (refund_count / metrics.order_count * 100) if metrics.order_count > 0 else 0, 1
        )

        return metrics
