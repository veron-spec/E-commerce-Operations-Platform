"""订单管理 API - 列表查询、筛选、分页。"""
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, verify_store_access
from app.models.order import Order
from app.models.user import User

router = APIRouter()


@router.get("", summary="订单列表", description="分页查询订单列表，支持状态筛选和关键词搜索")
async def list_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: str | None = Query(None, description="财务状态筛选：paid / refunded / pending"),
    search: str | None = Query(None, description="搜索订单号或买家邮箱"),
    store_id: int | None = Query(None, description="店铺ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Base query
    base_query = select(Order)
    count_query = select(func.count(Order.id))

    # User data isolation - scope to user's stores
    store_ids = await verify_store_access(store_id, user, db)
    base_query = base_query.where(Order.store_id.in_(store_ids))
    count_query = count_query.where(Order.store_id.in_(store_ids))

    # Filters
    if status:
        base_query = base_query.where(Order.financial_status == status)
        count_query = count_query.where(Order.financial_status == status)
    if search:
        like = f"%{search}%"
        filter_cond = or_(Order.order_number.ilike(like), Order.email.ilike(like))
        base_query = base_query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    total_pages = max(1, ceil(total / page_size))

    # Paginated query
    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
    )
    orders = result.scalars().all()

    return {
        "orders": [
            {
                "id": o.id,
                "store_id": o.store_id,
                "platform_id": o.platform_id,
                "order_number": o.order_number,
                "email": o.email,
                "line_items": o.line_items or [],
                "total_price": o.total_price,
                "subtotal_price": o.subtotal_price,
                "total_discount": o.total_discount,
                "financial_status": o.financial_status,
                "fulfillment_status": o.fulfillment_status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
