from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.analytics.sales import SalesAnalyzer
from app.core.analytics.inventory import InventoryAnalyzer
from app.core.analytics.trends import TrendAnalyzer
from app.models.order import Order

router = APIRouter()


@router.get("/sales", summary="销售分析", description="按日/周/月聚合的销售数据：收入、订单数、折扣金额")
async def sales_analysis(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    store_id: int | None = Query(None, description="店铺ID"),
    granularity: str = Query("day", pattern="^(day|week|month)$", description="聚合粒度：day=按天, week=按周, month=按月"),
    db: AsyncSession = Depends(get_db),
):
    analyzer = SalesAnalyzer(db)
    result = await analyzer.analyze(days=days, store_id=store_id, granularity=granularity)
    return result


@router.get("/inventory", summary="库存分析", description="库存状况分析：缺货商品、低库存预警、品类分布")
async def inventory_analysis(
    store_id: int | None = Query(None, description="店铺ID"),
    low_stock_threshold: int = Query(10, ge=0, description="低库存预警阈值"),
    db: AsyncSession = Depends(get_db),
):
    analyzer = InventoryAnalyzer(db)
    result = await analyzer.analyze(store_id=store_id, low_stock_threshold=low_stock_threshold)
    return result


@router.get("/trends", summary="趋势分析", description="环比/同比增长分析：收入增长率、订单增长率、每日趋势")
async def trend_analysis(
    days: int = Query(60, ge=14, le=730, description="分析周期天数"),
    store_id: int | None = Query(None, description="店铺ID"),
    db: AsyncSession = Depends(get_db),
):
    analyzer = TrendAnalyzer(db)
    result = await analyzer.analyze(days=days, store_id=store_id)
    return result


@router.get("/products/top", summary="畅销商品排行", description="按销售额排名的 Top N 畅销商品")
async def top_products(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    store_id: int | None = Query(None, description="店铺ID"),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    stmt = select(Order.line_items).where(Order.created_at >= since)
    if store_id:
        stmt = stmt.where(Order.store_id == store_id)

    result = await db.execute(stmt)
    rows = result.all()

    product_sales = {}
    for row in rows:
        items = row.line_items or []
        for item in items:
            pid = item.get("product_id") or item.get("sku", "unknown")
            if pid not in product_sales:
                product_sales[pid] = {
                    "title": item.get("title", "未知"),
                    "quantity": 0,
                    "revenue": 0,
                }
            product_sales[pid]["quantity"] += item.get("quantity", 0)
            product_sales[pid]["revenue"] += float(item.get("price", 0)) * item.get("quantity", 0)

    sorted_products = sorted(product_sales.values(), key=lambda x: x["revenue"], reverse=True)[:limit]
    return {"top_products": sorted_products, "period_days": days}
