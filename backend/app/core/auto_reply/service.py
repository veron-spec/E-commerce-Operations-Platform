"""Auto-reply service - keyword matching and reply management."""
import re
from datetime import UTC, datetime
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auto_reply import AutoReply


class AutoReplyService:
    """Manage auto-reply rules and match incoming messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(self, data: dict) -> dict:
        rule = AutoReply(
            store_id=data["store_id"],
            name=data["name"],
            trigger_keywords=data.get("trigger_keywords", []),
            match_type=data.get("match_type", "contains"),
            reply_template=data["reply_template"],
            priority=data.get("priority", 0),
            is_enabled=data.get("is_enabled", True),
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return self._to_dict(rule)

    async def update_rule(self, rule_id: int, data: dict) -> dict | None:
        result = await self.db.execute(select(AutoReply).where(AutoReply.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return None
        for key in ("name", "trigger_keywords", "match_type", "reply_template", "priority", "is_enabled", "store_id"):
            if key in data and data[key] is not None:
                setattr(rule, key, data[key])
        await self.db.commit()
        await self.db.refresh(rule)
        return self._to_dict(rule)

    async def delete_rule(self, rule_id: int) -> bool:
        result = await self.db.execute(select(AutoReply).where(AutoReply.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return False
        await self.db.delete(rule)
        await self.db.commit()
        return True

    async def list_rules(
        self,
        page: int = 1,
        page_size: int = 20,
        is_enabled: bool | None = None,
        match_type: str | None = None,
        store_ids: list[int] | None = None,
    ) -> dict:
        query = select(AutoReply)
        count_query = select(func.count(AutoReply.id))

        if store_ids:
            query = query.where(AutoReply.store_id.in_(store_ids))
            count_query = count_query.where(AutoReply.store_id.in_(store_ids))
        if is_enabled is not None:
            query = query.where(AutoReply.is_enabled == is_enabled)
            count_query = count_query.where(AutoReply.is_enabled == is_enabled)
        if match_type:
            query = query.where(AutoReply.match_type == match_type)
            count_query = count_query.where(AutoReply.match_type == match_type)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        total_pages = max(1, ceil(total / page_size))

        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(AutoReply.priority.desc(), AutoReply.created_at.desc())
            .offset(offset).limit(page_size)
        )
        rules = result.scalars().all()

        return {
            "items": [self._to_dict(r) for r in rules],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_rule(self, rule_id: int) -> dict | None:
        result = await self.db.execute(select(AutoReply).where(AutoReply.id == rule_id))
        rule = result.scalar_one_or_none()
        return self._to_dict(rule) if rule else None

    async def toggle_rule(self, rule_id: int) -> dict | None:
        result = await self.db.execute(select(AutoReply).where(AutoReply.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return None
        rule.is_enabled = not rule.is_enabled
        await self.db.commit()
        await self.db.refresh(rule)
        return self._to_dict(rule)

    async def test_match(self, message: str) -> dict:
        """Match a message against enabled rules, return highest-priority match."""
        result = await self.db.execute(
            select(AutoReply).where(AutoReply.is_enabled == True).order_by(AutoReply.priority.desc())
        )
        rules = result.scalars().all()

        for rule in rules:
            for keyword in (rule.trigger_keywords or []):
                matched = False
                if rule.match_type == "exact":
                    matched = message.strip() == keyword.strip()
                elif rule.match_type == "contains":
                    matched = keyword.lower() in message.lower()
                elif rule.match_type == "regex":
                    try:
                        matched = bool(re.search(keyword, message))
                    except re.error:
                        continue

                if matched:
                    # Increment usage
                    rule.usage_count = (rule.usage_count or 0) + 1
                    rule.last_used_at = datetime.now(UTC)
                    await self.db.commit()
                    await self.db.refresh(rule)

                    return {
                        "matched": True,
                        "rule": self._to_dict(rule),
                        "reply": rule.reply_template,
                    }

        return {"matched": False, "rule": None, "reply": None}

    async def get_match_stats(self, store_ids: list[int] | None = None) -> dict:
        query = select(AutoReply)
        if store_ids:
            query = query.where(AutoReply.store_id.in_(store_ids))
        result = await self.db.execute(query)
        rules = result.scalars().all()
        return {
            "total_rules": len(rules),
            "enabled": sum(1 for r in rules if r.is_enabled),
            "total_usage": sum(r.usage_count or 0 for r in rules),
        }

    def _to_dict(self, r: AutoReply) -> dict:
        return {
            "id": r.id,
            "store_id": r.store_id,
            "name": r.name,
            "trigger_keywords": r.trigger_keywords or [],
            "match_type": r.match_type,
            "reply_template": r.reply_template,
            "priority": r.priority,
            "is_enabled": r.is_enabled,
            "usage_count": r.usage_count or 0,
            "last_used_at": r.last_used_at.isoformat() if r.last_used_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
