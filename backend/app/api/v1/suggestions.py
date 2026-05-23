"""运营建议 API - 建议列表、生成、标记。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.suggestion.service import SuggestionService

router = APIRouter()


@router.get("", summary="建议列表")
async def list_suggestions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    suggestion_type: str | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    service = SuggestionService(db)
    return await service.list_suggestions(
        page=page, page_size=page_size,
        suggestion_type=suggestion_type, status=status, priority=priority,
        sort_by=sort_by, sort_desc=sort_desc,
    )


@router.get("/stats", summary="建议统计")
async def suggestion_stats(db: AsyncSession = Depends(get_db)):
    service = SuggestionService(db)
    return await service.get_suggestion_stats()


@router.post("/generate", summary="生成运营建议")
async def generate(
    store_id: int = Query(1, description="店铺ID"),
    db: AsyncSession = Depends(get_db),
):
    service = SuggestionService(db)
    results = await service.generate_suggestions(store_id)
    return {"generated": len(results), "items": results}


@router.get("/{suggestion_id}", summary="建议详情")
async def get_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db)):
    service = SuggestionService(db)
    result = await service.get_suggestion(suggestion_id)
    if not result:
        return {"error": "建议不存在"}, 404
    return result


@router.post("/{suggestion_id}/apply", summary="标记为已应用")
async def apply_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db)):
    service = SuggestionService(db)
    result = await service.mark_applied(suggestion_id)
    if not result:
        return {"error": "建议不存在"}, 404
    return result


@router.post("/{suggestion_id}/dismiss", summary="标记为已忽略")
async def dismiss_suggestion(suggestion_id: int, db: AsyncSession = Depends(get_db)):
    service = SuggestionService(db)
    result = await service.mark_dismissed(suggestion_id)
    if not result:
        return {"error": "建议不存在"}, 404
    return result
