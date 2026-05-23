"""Operations suggestions service - analyzes data and generates actionable suggestions."""
from datetime import datetime, timezone
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics.inventory import InventoryAnalyzer
from app.core.analytics.sales import SalesAnalyzer
from app.core.analytics.trends import TrendAnalyzer
from app.models.suggestion import Suggestion


class SuggestionService:
    """Generate and manage data-driven operational suggestions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_suggestions(
        self,
        page: int = 1,
        page_size: int = 20,
        suggestion_type: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> dict:
        query = select(Suggestion)
        count_query = select(func.count(Suggestion.id))

        if suggestion_type:
            query = query.where(Suggestion.suggestion_type == suggestion_type)
            count_query = count_query.where(Suggestion.suggestion_type == suggestion_type)
        if status:
            query = query.where(Suggestion.status == status)
            count_query = count_query.where(Suggestion.status == status)
        if priority:
            query = query.where(Suggestion.priority == priority)
            count_query = count_query.where(Suggestion.priority == priority)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        total_pages = max(1, ceil(total / page_size))

        sort_col = getattr(Suggestion, sort_by, Suggestion.created_at)
        order_fn = sort_col.desc() if sort_desc else sort_col.asc()
        offset = (page - 1) * page_size

        result = await self.db.execute(
            query.order_by(order_fn).offset(offset).limit(page_size)
        )
        items = result.scalars().all()

        return {
            "items": [self._to_dict(s) for s in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_suggestion(self, suggestion_id: int) -> dict | None:
        result = await self.db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
        s = result.scalar_one_or_none()
        return self._to_dict(s) if s else None

    async def mark_applied(self, suggestion_id: int) -> dict | None:
        result = await self.db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
        s = result.scalar_one_or_none()
        if not s:
            return None
        s.status = "applied"
        s.applied_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(s)
        return self._to_dict(s)

    async def mark_dismissed(self, suggestion_id: int) -> dict | None:
        result = await self.db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
        s = result.scalar_one_or_none()
        if not s:
            return None
        s.status = "dismissed"
        s.dismissed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(s)
        return self._to_dict(s)

    async def generate_suggestions(self, store_id: int = 1) -> list[dict]:
        """Analyze current data and generate suggestions if none exist for today."""
        inventory = InventoryAnalyzer(self.db)
        sales = SalesAnalyzer(self.db)
        trends = TrendAnalyzer(self.db)

        inv_data = await inventory.analyze(store_id=store_id)
        sales_data = await sales.analyze(store_id=store_id, days=30)
        trends_data = await trends.analyze(store_id=store_id, days=60)

        suggestions = []

        # 1. Restock suggestions from low stock items
        for item in (inv_data.low_stock_items or []):
            title = item.get("title", "Unknown")
            qty = item.get("quantity", 0)
            priority = "high" if qty <= 0 else "medium"
            dup_check = await self._exists("restock", f"补货提醒 - {title}")
            if not dup_check:
                suggestions.append(Suggestion(
                    store_id=store_id,
                    suggestion_type="restock",
                    title=f"补货提醒 - {title}",
                    description=f"商品 \"{title}\" 当前库存仅 {qty} 件，建议尽快补货以避免缺货。",
                    priority=priority,
                    data_source="inventory_analyzer",
                    related_metrics={"current_stock": qty, "category": item.get("category")},
                ))

        # 2. Price adjustment suggestions
        for item in (inv_data.low_stock_items or []):
            if item.get("quantity", 0) <= 0:
                continue
            title = item.get("title", "Unknown")
            qty = item.get("quantity", 0)
            dup_check = await self._exists("price_adjustment", f"价格调整 - {title}")
            if not dup_check:
                suggestions.append(Suggestion(
                    store_id=store_id,
                    suggestion_type="price_adjustment",
                    title=f"价格调整 - {title}",
                    description=f"商品 \"{title}\" 库存偏低 ({qty} 件)，销量稳定，可考虑适当提价测试市场反应。",
                    priority="low",
                    data_source="sales_analyzer",
                    related_metrics={"current_stock": qty, "suggestion": "提价5-10%"},
                ))

        # 3. Marketing campaign for trending products
        if trends_data:
            rev_growth = trends_data.revenue_growth_pct or 0
            order_growth = trends_data.order_growth_pct or 0
            if rev_growth > 10 or order_growth > 10:
                dup_check = await self._exists("marketing_campaign", "营销活动建议")
                if not dup_check:
                    suggestions.append(Suggestion(
                        store_id=store_id,
                        suggestion_type="marketing_campaign",
                        title="营销活动建议",
                        description=f"近期销售额增长 {rev_growth:.1f}%，订单量增长 {order_growth:.1f}%，建议加大推广力度以抓住增长趋势。",
                        priority="high" if rev_growth > 20 else "medium",
                        data_source="trend_analyzer",
                        related_metrics={"revenue_growth_pct": round(rev_growth, 1), "order_growth_pct": round(order_growth, 1)},
                    ))

        # 4. Inventory optimization for overstock
        for item in (inv_data.low_stock_items or []):
            qty = item.get("quantity", 0)
            if qty > 100:
                title = item.get("title", "Unknown")
                dup_check = await self._exists("inventory_optimization", f"库存优化 - {title}")
                if not dup_check:
                    suggestions.append(Suggestion(
                        store_id=store_id,
                        suggestion_type="inventory_optimization",
                        title=f"库存优化 - {title}",
                        description=f"商品 \"{title}\" 库存量较大 ({qty} 件)，建议通过促销活动清理库存，释放仓储空间。",
                        priority="low",
                        data_source="inventory_analyzer",
                        related_metrics={"current_stock": qty},
                    ))

        # Save all suggestions
        saved = []
        for s in suggestions:
            self.db.add(s)
            saved.append(s)
        if saved:
            await self.db.commit()
            for s in saved:
                await self.db.refresh(s)

        return [self._to_dict(s) for s in saved]

    async def get_suggestion_stats(self) -> dict:
        result = await self.db.execute(select(Suggestion))
        all_items = result.scalars().all()

        total = len(all_items)
        by_type: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        by_status: dict[str, int] = {}
        applied = 0

        for s in all_items:
            by_type[s.suggestion_type] = by_type.get(s.suggestion_type, 0) + 1
            by_priority[s.priority] = by_priority.get(s.priority, 0) + 1
            by_status[s.status] = by_status.get(s.status, 0) + 1
            if s.status == "applied":
                applied += 1

        return {
            "total": total,
            "by_type": by_type,
            "by_priority": by_priority,
            "by_status": by_status,
            "applied_rate": round(applied / total * 100, 1) if total > 0 else 0,
        }

    async def _exists(self, stype: str, title: str) -> bool:
        result = await self.db.execute(
            select(func.count(Suggestion.id)).where(
                Suggestion.suggestion_type == stype,
                Suggestion.title == title,
                Suggestion.status == "pending",
            )
        )
        return (result.scalar() or 0) > 0

    def _to_dict(self, s: Suggestion) -> dict:
        return {
            "id": s.id,
            "store_id": s.store_id,
            "suggestion_type": s.suggestion_type,
            "title": s.title,
            "description": s.description,
            "priority": s.priority,
            "data_source": s.data_source,
            "related_metrics": s.related_metrics or {},
            "status": s.status,
            "applied_at": s.applied_at.isoformat() if s.applied_at else None,
            "dismissed_at": s.dismissed_at.isoformat() if s.dismissed_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
