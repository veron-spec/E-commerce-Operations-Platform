"""Retrospective analysis service - period-based performance reviews."""
from datetime import UTC, datetime, timedelta
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics.inventory import InventoryAnalyzer
from app.core.analytics.sales import SalesAnalyzer
from app.core.analytics.trends import TrendAnalyzer
from app.models.retrospective import Retrospective


class RetrospectiveService:
    """Generate and manage period-based business retrospectives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_retrospectives(
        self,
        page: int = 1,
        page_size: int = 20,
        period_type: str | None = None,
        status: str | None = None,
        sort_desc: bool = True,
        store_ids: list[int] | None = None,
    ) -> dict:
        query = select(Retrospective)
        count_query = select(func.count(Retrospective.id))

        if store_ids:
            query = query.where(Retrospective.store_id.in_(store_ids))
            count_query = count_query.where(Retrospective.store_id.in_(store_ids))
        if period_type:
            query = query.where(Retrospective.period_type == period_type)
            count_query = count_query.where(Retrospective.period_type == period_type)
        if status:
            query = query.where(Retrospective.status == status)
            count_query = count_query.where(Retrospective.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        total_pages = max(1, ceil(total / page_size))

        order_fn = Retrospective.period_start.desc() if sort_desc else Retrospective.period_start.asc()
        offset = (page - 1) * page_size

        result = await self.db.execute(
            query.order_by(order_fn).offset(offset).limit(page_size)
        )
        items = result.scalars().all()

        return {
            "items": [self._to_dict(r, summary=True) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_retrospective(self, retro_id: int) -> dict | None:
        result = await self.db.execute(select(Retrospective).where(Retrospective.id == retro_id))
        r = result.scalar_one_or_none()
        return self._to_dict(r) if r else None

    async def generate(
        self,
        store_id: int = 1,
        period_type: str = "weekly",
    ) -> dict:
        """Generate a retrospective for the given period type."""
        now = datetime.now(UTC)

        if period_type == "weekly":
            period_end = now - timedelta(days=now.weekday())  # end of last week
            period_start = period_end - timedelta(days=7)
            prev_start = period_start - timedelta(days=7)
        elif period_type == "monthly":
            period_end = now.replace(day=1) - timedelta(days=1)  # last day of prev month
            period_start = period_end.replace(day=1)  # first day of prev month
            prev_start = (period_start - timedelta(days=1)).replace(day=1)
        elif period_type == "quarterly":
            quarter_month = ((now.month - 1) // 3) * 3
            period_end = datetime(now.year, quarter_month + 1, 1, tzinfo=UTC) - timedelta(days=1)
            period_start = datetime(now.year, quarter_month - 2, 1, tzinfo=UTC)
            prev_start = (period_start - timedelta(days=1)).replace(day=1) - timedelta(days=90)
        else:
            raise ValueError(f"Unsupported period_type: {period_type}")

        # Check for existing
        existing = await self.db.execute(
            select(Retrospective).where(
                Retrospective.store_id == store_id,
                Retrospective.period_type == period_type,
                Retrospective.period_start == period_start,
            )
        )
        if existing.scalar_one_or_none():
            return {"error": f"该{period_type}复盘已存在"}

        # Gather data
        sales = SalesAnalyzer(self.db)
        inventory = InventoryAnalyzer(self.db)
        trends = TrendAnalyzer(self.db)

        current_sales = await sales.analyze(store_id=store_id, days=7)
        inv_data = await inventory.analyze(store_id=store_id)
        trend_data = await trends.analyze(store_id=store_id, days=60)

        # Compute summary
        total_revenue = sum((d.get("revenue") or 0) for d in (current_sales.revenue_by_day or []))
        total_orders = sum((d.get("order_count") or 0) for d in (current_sales.revenue_by_day or []))
        avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0
        refund_rate = round(current_sales.refund_rate or 0, 1)

        data_summary = {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "avg_order_value": avg_order_value,
            "refund_rate": refund_rate,
            "low_stock_count": inv_data.low_stock_count or 0,
            "out_of_stock_count": inv_data.out_of_stock_count or 0,
        }

        # Build metrics snapshot
        metrics_snapshot = {
            "revenue_by_day": [(d["period"], d["revenue"], d["order_count"]) for d in (current_sales.revenue_by_day or [])],
            "category_distribution": inv_data.category_distribution or [],
            "total_products": inv_data.total_products or 0,
        }

        # Comparisons
        comparisons = {}
        if trend_data:
            comparisons = {
                "revenue_change_pct": round(trend_data.revenue_growth_pct or 0, 1),
                "order_change_pct": round(trend_data.order_growth_pct or 0, 1),
            }

        # Insights
        insights = []
        if trend_data:
            rg = trend_data.revenue_growth_pct or 0
            if rg > 10:
                insights.append(f"销售额环比增长 {rg:.1f}%，表现良好")
            elif rg < -10:
                insights.append(f"销售额环比下降 {rg:.1f}%，需要关注")

        if inv_data.low_stock_count and inv_data.low_stock_count > 0:
            insights.append(f"{inv_data.low_stock_count} 款商品库存不足，其中 {inv_data.out_of_stock_count} 款已缺货")
        if inv_data.out_of_stock_count and inv_data.out_of_stock_count > 0:
            insights.append(f"缺货商品 {inv_data.out_of_stock_count} 款，建议优先补货")
        if refund_rate > 10:
            insights.append(f"退款率 {refund_rate}%，偏高，建议排查原因")

        # Action items
        action_items = []
        if inv_data.low_stock_items:
            low_items = [i.get("title") for i in (inv_data.low_stock_items or []) if i.get("title")]
            if low_items:
                action_items.append(f"补货提醒：{'、'.join(low_items[:5])}")
        if refund_rate > 10:
            action_items.append("排查退款原因，优化商品描述或质量")

        if not insights:
            insights.append("运营数据总体平稳")

        # Create record
        retro = Retrospective(
            store_id=store_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            data_summary=data_summary,
            metrics_snapshot=metrics_snapshot,
            comparisons=comparisons,
            insights=insights,
            action_items=action_items,
            status="draft",
        )
        self.db.add(retro)
        await self.db.commit()
        await self.db.refresh(retro)
        return self._to_dict(retro)

    async def publish(self, retro_id: int) -> dict | None:
        result = await self.db.execute(select(Retrospective).where(Retrospective.id == retro_id))
        r = result.scalar_one_or_none()
        if not r:
            return None
        r.status = "published"
        r.published_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(r)
        return self._to_dict(r)

    async def get_stats(self, store_ids: list[int] | None = None) -> dict:
        query = select(Retrospective).order_by(Retrospective.period_start.desc())
        if store_ids:
            query = query.where(Retrospective.store_id.in_(store_ids))
        result = await self.db.execute(query)
        items = result.scalars().all()

        by_type: dict[str, int] = {}
        latest = None
        for r in items:
            by_type[r.period_type] = by_type.get(r.period_type, 0) + 1
            if latest is None:
                latest = self._to_dict(r)

        return {
            "total": len(items),
            "by_type": by_type,
            "latest": latest,
        }

    def _to_dict(self, r: Retrospective, summary: bool = False) -> dict:
        base = {
            "id": r.id,
            "store_id": r.store_id,
            "period_type": r.period_type,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "data_summary": r.data_summary or {},
            "status": r.status,
            "published_at": r.published_at.isoformat() if r.published_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        if not summary:
            base.update({
                "metrics_snapshot": r.metrics_snapshot or {},
                "comparisons": r.comparisons or {},
                "insights": r.insights or [],
                "action_items": r.action_items or [],
            })
        return base
