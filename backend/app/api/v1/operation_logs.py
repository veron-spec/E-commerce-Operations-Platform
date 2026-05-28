"""API routes for operation logs — audit trail viewer."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, verify_store_access
from app.models.operation_log import OperationLog
from app.models.user import User

router = APIRouter()


@router.get("/operation-logs", summary="操作日志", description="查询当前用户的操作日志")
async def list_operation_logs(
    action: str | None = Query(None, description="按操作类型筛选（create/update/delete/login）"),
    resource_type: str | None = Query(None, description="按资源类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(OperationLog).where(OperationLog.user_id == user.id)
    count_query = select(func.count(OperationLog.id)).where(OperationLog.user_id == user.id)

    if action:
        query = query.where(OperationLog.action == action)
        count_query = count_query.where(OperationLog.action == action)
    if resource_type:
        query = query.where(OperationLog.resource_type == resource_type)
        count_query = count_query.where(OperationLog.resource_type == resource_type)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(desc(OperationLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    results = (await db.execute(query)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in results
        ],
    }


@router.get("/operation-logs/latest", summary="最近操作", description="当前用户最近的 10 条操作")
async def latest_operations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(OperationLog)
        .where(OperationLog.user_id == user.id)
        .order_by(desc(OperationLog.created_at))
        .limit(10)
    )
    results = (await db.execute(query)).scalars().all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": log.detail,
            "created_at": log.created_at.isoformat(),
        }
        for log in results
    ]
