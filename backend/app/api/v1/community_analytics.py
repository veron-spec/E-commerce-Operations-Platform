"""Community Edition fallback endpoints for analytics — return empty data structures
so the UI doesn't show 404 errors for Pro-only analytics routes."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.order import Order
from app.models.user import User

router = APIRouter()


@router.get("/sales")
async def sales_analysis(
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {"revenue_by_day": [], "total_revenue": 0, "total_orders": 0, "period_days": days}


@router.get("/inventory")
async def inventory_analysis(
    low_stock_threshold: int = Query(10, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {
        "total_products": 0,
        "low_stock_count": 0,
        "out_of_stock_count": 0,
        "category_distribution": [],
        "low_stock_items": [],
    }


@router.get("/trends")
async def trend_analysis(
    days: int = Query(60, ge=14, le=730),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {"growth_rates": {}, "period_days": days}


@router.get("/products/top")
async def top_products(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {"top_products": [], "period_days": days}
