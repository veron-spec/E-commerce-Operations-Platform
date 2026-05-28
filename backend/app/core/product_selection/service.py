"""Product selection service - CRUD and scanning logic."""
from datetime import datetime
from math import ceil

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.product_selection.analyzer import ProductSelectionAnalyzer
from app.models.product_selection import ProductSelection


class ProductSelectionService:
    """Service for managing product selection candidates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_selection(self, data: dict) -> dict:
        selection = ProductSelection(
            store_id=data.get("store_id", 1),
            product_id=data.get("product_id"),
            title=data["title"],
            platform=data.get("platform", "taobao"),
            source=data.get("source", "manual"),
            category=data.get("category"),
            price=data.get("price", 0),
            sales_volume=data.get("sales_volume", 0),
            growth_rate=data.get("growth_rate", 0),
            margin=data.get("margin", 0),
            selection_score=data.get("selection_score", 0),
            reason=data.get("reason"),
            status=data.get("status", "pending"),
            extra_data=data.get("extra_data", {}),
        )
        self.db.add(selection)
        await self.db.commit()
        await self.db.refresh(selection)
        return self._to_dict(selection)

    async def list_selections(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        category: str | None = None,
        source: str | None = None,
        score_min: float | None = None,
        score_max: float | None = None,
        sort_by: str = "selection_score",
        sort_desc: bool = True,
    ) -> dict:
        query = select(ProductSelection)
        count_query = select(func.count(ProductSelection.id))

        if status:
            query = query.where(ProductSelection.status == status)
            count_query = count_query.where(ProductSelection.status == status)
        if category:
            query = query.where(ProductSelection.category == category)
            count_query = count_query.where(ProductSelection.category == category)
        if source:
            query = query.where(ProductSelection.source == source)
            count_query = count_query.where(ProductSelection.source == source)
        if score_min is not None:
            query = query.where(ProductSelection.selection_score >= score_min)
            count_query = count_query.where(ProductSelection.selection_score >= score_min)
        if score_max is not None:
            query = query.where(ProductSelection.selection_score <= score_max)
            count_query = count_query.where(ProductSelection.selection_score <= score_max)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        total_pages = max(1, ceil(total / page_size))

        sort_col = getattr(ProductSelection, sort_by, ProductSelection.selection_score)
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

    async def get_selection(self, selection_id: int) -> dict | None:
        result = await self.db.execute(
            select(ProductSelection).where(ProductSelection.id == selection_id)
        )
        selection = result.scalar_one_or_none()
        return self._to_dict(selection) if selection else None

    async def update_selection(self, selection_id: int, data: dict) -> dict | None:
        result = await self.db.execute(
            select(ProductSelection).where(ProductSelection.id == selection_id)
        )
        selection = result.scalar_one_or_none()
        if not selection:
            return None

        for key, val in data.items():
            if hasattr(selection, key) and val is not None:
                setattr(selection, key, val)
        await self.db.commit()
        await self.db.refresh(selection)
        return self._to_dict(selection)

    async def delete_selection(self, selection_id: int) -> bool:
        result = await self.db.execute(
            select(ProductSelection).where(ProductSelection.id == selection_id)
        )
        selection = result.scalar_one_or_none()
        if not selection:
            return False
        await self.db.delete(selection)
        await self.db.commit()
        return True

    async def scan_for_winners(self, store_id: int = 1) -> list[dict]:
        """Run analytics scan and save qualifying candidates."""
        analyzer = ProductSelectionAnalyzer(self.db)
        candidates = await analyzer.scan_for_winners(store_id)

        saved = []
        for c in candidates:
            # Avoid duplicates for same product
            existing = await self.db.execute(
                select(ProductSelection).where(
                    ProductSelection.store_id == store_id,
                    ProductSelection.product_id == c["product_id"],
                    ProductSelection.status.in_(["pending", "approved"]),
                )
            )
            if existing.scalar_one_or_none():
                continue
            sel = await self.add_selection({**c, "store_id": store_id, "source": "analytics"})
            saved.append(sel)

        return saved

    async def get_selection_stats(self) -> dict:
        result = await self.db.execute(select(ProductSelection))
        all_items = result.scalars().all()
        total = len(all_items)
        pending = sum(1 for s in all_items if s.status == "pending")
        approved = sum(1 for s in all_items if s.status == "approved")
        rejected = sum(1 for s in all_items if s.status == "rejected")
        avg_score = round(
            sum(s.selection_score for s in all_items) / total, 1
        ) if total > 0 else 0

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "avg_score": avg_score,
        }

    def _to_dict(self, s: ProductSelection) -> dict:
        return {
            "id": s.id,
            "store_id": s.store_id,
            "product_id": s.product_id,
            "title": s.title,
            "platform": s.platform,
            "source": s.source,
            "category": s.category or "",
            "price": s.price,
            "sales_volume": s.sales_volume,
            "growth_rate": s.growth_rate,
            "margin": s.margin,
            "selection_score": s.selection_score,
            "reason": s.reason or "",
            "status": s.status,
            "extra_data": s.extra_data or {},
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
