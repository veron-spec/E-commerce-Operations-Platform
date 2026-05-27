from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db,
    verify_store_access,
)
from app.infrastructure.cache import cached
from app.models.order import Order
from app.models.product import Product
from app.models.user import User

router = APIRouter()


@router.get("/summary", summary="看板总览", description="获取销售总览数据")
@cached(ttl=120, prefix="dashboard:summary")
async def dashboard_summary(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    store_id: int | None = Query(None, description="店铺ID，不传则统计所有店铺"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await verify_store_access(store_id, user, db)

    since = datetime.now(UTC) - timedelta(days=days)

    # Total sales
    query = select(func.coalesce(func.sum(Order.total_price), 0)).where(
        Order.created_at >= since, Order.store_id.in_(store_ids)
    )
    total_sales = (await db.execute(query)).scalar()

    # Order count
    query = select(func.count(Order.id)).where(
        Order.created_at >= since, Order.store_id.in_(store_ids)
    )
    order_count = (await db.execute(query)).scalar()

    # Product count (scoped to user's stores)
    query = select(func.count(Product.id)).where(Product.store_id.in_(store_ids))
    total_products = (await db.execute(query)).scalar()

    avg_order_value = round(total_sales / order_count, 2) if order_count else 0

    return {
        "period_days": days,
        "total_sales": float(total_sales),
        "order_count": order_count,
        "total_products": total_products,
        "avg_order_value": avg_order_value,
    }
