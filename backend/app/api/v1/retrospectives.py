"""复盘分析 API - 复盘列表、生成、发布。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_user_store_ids, verify_store_access
from app.models.user import User

try:
    from app.pro.retrospective.service import RetrospectiveService
except ImportError:
    RetrospectiveService = None

router = APIRouter()


@router.get("", summary="复盘列表")
async def list_retrospectives(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    period_type: str | None = Query(None, pattern="^(weekly|monthly|quarterly)$"),
    status: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    service = RetrospectiveService(db)
    return await service.list_retrospectives(
        page=page, page_size=page_size, period_type=period_type, status=status,
        store_ids=store_ids,
    )


@router.get("/stats", summary="复盘统计")
async def retrospective_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    service = RetrospectiveService(db)
    return await service.get_stats(store_ids=store_ids)


@router.post("/generate", summary="生成复盘分析", status_code=201)
async def generate_retrospective(
    store_id: int = Query(..., description="店铺ID"),
    period_type: str = Query("weekly", pattern="^(weekly|monthly|quarterly)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_store_access(store_id, user, db)
    service = RetrospectiveService(db)
    return await service.generate(store_id=store_id, period_type=period_type)


@router.get("/{retro_id}", summary="复盘详情")
async def get_retrospective(
    retro_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RetrospectiveService(db)
    result = await service.get_retrospective(retro_id)
    if not result:
        raise HTTPException(status_code=404, detail="复盘不存在")
    await verify_store_access(result["store_id"], user, db)
    return result


@router.post("/{retro_id}/publish", summary="发布复盘")
async def publish_retrospective(
    retro_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RetrospectiveService(db)
    result = await service.publish(retro_id)
    if not result:
        raise HTTPException(status_code=404, detail="复盘不存在")
    await verify_store_access(result["store_id"], user, db)
    return result
