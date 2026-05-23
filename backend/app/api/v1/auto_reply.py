"""自动化客服 API - 自动回复规则管理、消息测试。"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.auto_reply.service import AutoReplyService

router = APIRouter()


class CreateAutoReplyRequest(BaseModel):
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


@router.get("", summary="自动回复规则列表")
async def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_enabled: bool | None = Query(None),
    match_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AutoReplyService(db)
    return await service.list_rules(page=page, page_size=page_size, is_enabled=is_enabled, match_type=match_type)


@router.post("", summary="创建规则", status_code=201)
async def create_rule(req: CreateAutoReplyRequest, db: AsyncSession = Depends(get_db)):
    service = AutoReplyService(db)
    return await service.create_rule(req.model_dump())


@router.get("/stats", summary="匹配统计")
async def match_stats(db: AsyncSession = Depends(get_db)):
    service = AutoReplyService(db)
    return await service.get_match_stats()


@router.post("/test", summary="测试消息匹配")
async def test_match(req: TestMatchRequest, db: AsyncSession = Depends(get_db)):
    service = AutoReplyService(db)
    return await service.test_match(req.message)


@router.get("/{rule_id}", summary="规则详情")
async def get_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    service = AutoReplyService(db)
    result = await service.get_rule(rule_id)
    if not result:
        return {"error": "规则不存在"}, 404
    return result


@router.put("/{rule_id}", summary="更新规则")
async def update_rule(rule_id: int, req: UpdateAutoReplyRequest, db: AsyncSession = Depends(get_db)):
    service = AutoReplyService(db)
    result = await service.update_rule(rule_id, req.model_dump(exclude_none=True))
    if not result:
        return {"error": "规则不存在"}, 404
    return result


@router.delete("/{rule_id}", summary="删除规则", status_code=204)
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    service = AutoReplyService(db)
    ok = await service.delete_rule(rule_id)
    if not ok:
        return {"error": "规则不存在"}, 404


@router.post("/{rule_id}/toggle", summary="启用/停用规则")
async def toggle_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    service = AutoReplyService(db)
    result = await service.toggle_rule(rule_id)
    if not result:
        return {"error": "规则不存在"}, 404
    return result
