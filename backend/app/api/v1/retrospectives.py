"""复盘分析 API - 复盘列表、生成、发布。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.retrospective.service import RetrospectiveService

router = APIRouter()


@router.get("", summary="复盘列表")
async def list_retrospectives(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    period_type: str | None = Query(None, pattern="^(weekly|monthly|quarterly)$"),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = RetrospectiveService(db)
    return await service.list_retrospectives(
        page=page, page_size=page_size, period_type=period_type, status=status
    )


@router.get("/stats", summary="复盘统计")
async def retrospective_stats(db: AsyncSession = Depends(get_db)):
    service = RetrospectiveService(db)
    return await service.get_stats()


@router.post("/generate", summary="生成复盘分析", status_code=201)
async def generate_retrospective(
    store_id: int = Query(1),
    period_type: str = Query("weekly", pattern="^(weekly|monthly|quarterly)$"),
    db: AsyncSession = Depends(get_db),
):
    service = RetrospectiveService(db)
    return await service.generate(store_id=store_id, period_type=period_type)


@router.get("/{retro_id}", summary="复盘详情")
async def get_retrospective(retro_id: int, db: AsyncSession = Depends(get_db)):
    service = RetrospectiveService(db)
    result = await service.get_retrospective(retro_id)
    if not result:
        return {"error": "复盘不存在"}, 404
    return result


@router.post("/{retro_id}/publish", summary="发布复盘")
async def publish_retrospective(retro_id: int, db: AsyncSession = Depends(get_db)):
    service = RetrospectiveService(db)
    result = await service.publish(retro_id)
    if not result:
        return {"error": "复盘不存在"}, 404
    return result
