from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.order import Order
from app.models.product import Product

router = APIRouter()


@router.get("/summary", summary="看板总览", description="获取销售总览数据：总销售额、订单数、商品数、平均客单价")
async def dashboard_summary(
    days: int = Query(30, ge=1, le=365, description="统计天数（最近N天）"),
    store_id: int | None = Query(None, description="店铺ID，不传则统计所有店铺"),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    # Total sales
    query = select(func.coalesce(func.sum(Order.total_price), 0)).where(Order.created_at >= since)
    if store_id:
        query = query.where(Order.store_id == store_id)
    result = await db.execute(query)
    total_sales = result.scalar()

    # Order count
    query = select(func.count(Order.id)).where(Order.created_at >= since)
    if store_id:
        query = query.where(Order.store_id == store_id)
    result = await db.execute(query)
    order_count = result.scalar()

    # Product count
    result = await db.execute(select(func.count(Product.id)))
    total_products = result.scalar()

    # Average order value
    avg_order_value = round(total_sales / order_count, 2) if order_count else 0

    return {
        "period_days": days,
        "total_sales": float(total_sales),
        "order_count": order_count,
        "total_products": total_products,
        "avg_order_value": avg_order_value,
    }
