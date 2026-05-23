"""自动化规则 API - 规则列表、创建、启停。"""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.automation_rule import AutomationRule

router = APIRouter()


class CreateRuleRequest(BaseModel):
    name: str
    trigger_type: str = "scheduled"
    conditions: dict | None = None
    actions: list[dict] | None = None
    is_enabled: bool = True


@router.get("/rules", summary="规则列表", description="获取所有自动化规则")
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AutomationRule).order_by(AutomationRule.created_at.desc()))
    rules = result.scalars().all()

    active_count = sum(1 for r in rules if r.is_enabled)

    return {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "trigger_type": r.trigger_type,
                "conditions": r.conditions or {},
                "actions": r.actions or {},
                "is_enabled": r.is_enabled,
                "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rules
        ],
        "total": len(rules),
        "active_count": active_count,
    }


@router.post("/rules", summary="创建规则", description="创建一条自动化规则", status_code=201)
async def create_rule(req: CreateRuleRequest, db: AsyncSession = Depends(get_db)):
    rule = AutomationRule(
        store_id=1,  # Default to first store; TODO: support multi-store
        name=req.name,
        trigger_type=req.trigger_type,
        conditions=req.conditions or {},
        actions=req.actions or [],
        is_enabled=req.is_enabled,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"id": rule.id, "name": rule.name, "message": "规则创建成功"}


@router.post("/rules/{rule_id}/toggle", summary="切换规则状态", description="启用或停用指定规则")
async def toggle_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AutomationRule).where(AutomationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return {"error": "规则不存在"}, 404

    rule.is_enabled = not rule.is_enabled
    await db.commit()
    return {
        "id": rule.id,
        "is_enabled": rule.is_enabled,
        "message": "规则已启用" if rule.is_enabled else "规则已停用",
    }


@router.get("/rules/stats", summary="规则统计", description="获取规则运行统计")
async def rule_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AutomationRule))
    rules = result.scalars().all()
    active = sum(1 for r in rules if r.is_enabled)
    return {
        "total_rules": len(rules),
        "active_rules": active,
        "today_executions": 0,  # TODO: implement execution logging
    }
