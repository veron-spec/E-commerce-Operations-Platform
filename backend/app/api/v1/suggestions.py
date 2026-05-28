"""杩愯惀寤鸿 API - 寤鸿鍒楄〃銆佺敓鎴愩€佹爣璁般€?""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_user_store_ids, verify_store_access
from app.models.suggestion import Suggestion

try:
    from app.pro.suggestion.service import SuggestionService
except ImportError:
    SuggestionService = Nonefrom app.models.user import User

router = APIRouter()


async def _verify_suggestion_owner(suggestion_id: int, user: User, db: AsyncSession) -> Suggestion:
    """Verify the suggestion belongs to one of user's stores."""
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="寤鸿涓嶅瓨鍦?)
    await verify_store_access(suggestion.store_id, user, db)
    return suggestion


@router.get("", summary="寤鸿鍒楄〃")
async def list_suggestions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    suggestion_type: str | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    service = SuggestionService(db)
    return await service.list_suggestions(
        page=page, page_size=page_size,
        suggestion_type=suggestion_type, status=status, priority=priority,
        sort_by=sort_by, sort_desc=sort_desc, store_ids=store_ids,
    )


@router.get("/stats", summary="寤鸿缁熻")
async def suggestion_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    service = SuggestionService(db)
    return await service.get_suggestion_stats(store_ids=store_ids)


@router.post("/generate", summary="鐢熸垚杩愯惀寤鸿")
async def generate(
    store_id: int = Query(..., description="搴楅摵ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_store_access(store_id, user, db)
    service = SuggestionService(db)
    results = await service.generate_suggestions(store_id)
    return {"generated": len(results), "items": results}


@router.get("/{suggestion_id}", summary="寤鸿璇︽儏")
async def get_suggestion(
    suggestion_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_suggestion_owner(suggestion_id, user, db)
    service = SuggestionService(db)
    return await service.get_suggestion(suggestion_id)


@router.post("/{suggestion_id}/apply", summary="鏍囪涓哄凡搴旂敤")
async def apply_suggestion(
    suggestion_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    suggestion = await _verify_suggestion_owner(suggestion_id, user, db)
    service = SuggestionService(db)
    return await service.mark_applied(suggestion.id)


@router.post("/{suggestion_id}/dismiss", summary="鏍囪涓哄凡蹇界暐")
async def dismiss_suggestion(
    suggestion_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    suggestion = await _verify_suggestion_owner(suggestion_id, user, db)
    service = SuggestionService(db)
    return await service.mark_dismissed(suggestion.id)
