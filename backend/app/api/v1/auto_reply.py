"""鑷姩鍖栧鏈?API - 鑷姩鍥炲瑙勫垯绠＄悊銆佹秷鎭祴璇曘€?""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_user_store_ids, verify_store_access
from app.models.auto_reply import AutoReply

try:
    from app.pro.auto_reply.service import AutoReplyService
except ImportError:
    AutoReplyService = Nonefrom app.models.user import User

router = APIRouter()


class CreateAutoReplyRequest(BaseModel):
    store_id: int
    name: str
    trigger_keywords: list[str]
    match_type: str = "contains"
    reply_template: str
    priority: int = 0
    is_enabled: bool = True


class UpdateAutoReplyRequest(BaseModel):
    name: str | None = None
    trigger_keywords: list[str] | None = None
    match_type: str | None = None
    reply_template: str | None = None
    priority: int | None = None
    is_enabled: bool | None = None


class TestMatchRequest(BaseModel):
    message: str


async def _verify_rule_owner(rule_id: int, user: User, db: AsyncSession) -> AutoReply:
    """Verify the auto-reply rule belongs to one of user's stores."""
    result = await db.execute(select(AutoReply).where(AutoReply.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="瑙勫垯涓嶅瓨鍦?)
    await verify_store_access(rule.store_id, user, db)
    return rule


@router.get("", summary="鑷姩鍥炲瑙勫垯鍒楄〃")
async def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_enabled: bool | None = Query(None),
    match_type: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    if not store_ids:
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
    service = AutoReplyService(db)
    return await service.list_rules(
        page=page, page_size=page_size, is_enabled=is_enabled,
        match_type=match_type, store_ids=store_ids,
    )


@router.post("", summary="鍒涘缓瑙勫垯", status_code=201)
async def create_rule(
    req: CreateAutoReplyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_store_access(req.store_id, user, db)
    service = AutoReplyService(db)
    return await service.create_rule(req.model_dump())


@router.get("/stats", summary="鍖归厤缁熻")
async def match_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    if not store_ids:
        return {"total_rules": 0, "enabled": 0, "total_usage": 0}
    service = AutoReplyService(db)
    return await service.get_match_stats(store_ids=store_ids)


@router.post("/test", summary="娴嬭瘯娑堟伅鍖归厤")
async def test_match(
    req: TestMatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AutoReplyService(db)
    return await service.test_match(req.message)


@router.get("/{rule_id}", summary="瑙勫垯璇︽儏")
async def get_rule(
    rule_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await _verify_rule_owner(rule_id, user, db)
    service = AutoReplyService(db)
    return await service.get_rule(rule_id)


@router.put("/{rule_id}", summary="鏇存柊瑙勫垯")
async def update_rule(
    rule_id: int,
    req: UpdateAutoReplyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_rule_owner(rule_id, user, db)
    service = AutoReplyService(db)
    result = await service.update_rule(rule_id, req.model_dump(exclude_none=True))
    return result


@router.delete("/{rule_id}", summary="鍒犻櫎瑙勫垯", status_code=204)
async def delete_rule(
    rule_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_rule_owner(rule_id, user, db)
    service = AutoReplyService(db)
    await service.delete_rule(rule_id)


@router.post("/{rule_id}/toggle", summary="鍚敤/鍋滅敤瑙勫垯")
async def toggle_rule(
    rule_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_rule_owner(rule_id, user, db)
    service = AutoReplyService(db)
    return await service.toggle_rule(rule_id)
