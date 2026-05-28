"""API tests for automation rules — CRUD, toggle, stats, isolation."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAutomation:
    async def test_create_rule(self, client: AsyncClient, test_store):
        response = await client.post("/api/v1/automation/rules", json={
            "store_id": test_store["id"],
            "name": "测试规则",
            "trigger_type": "scheduled",
            "conditions": {"key": "value"},
            "actions": [{"type": "notify"}],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试规则"
        assert "id" in data

    async def test_create_rule_wrong_store(self, client: AsyncClient, second_store):
        response = await client.post("/api/v1/automation/rules", json={
            "store_id": second_store["id"],
            "name": "越权规则",
            "trigger_type": "scheduled",
        })
        assert response.status_code == 404

    async def test_list_rules(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/automation/rules")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "total" in data

    async def test_toggle_rule(self, client: AsyncClient, db: AsyncSession, test_store):
        from app.models.automation_rule import AutomationRule
        rule = AutomationRule(
            store_id=test_store["id"],
            name="Toggle Test",
            trigger_type="scheduled",
        )
        db.add(rule)
        await db.commit()
        rule_id = rule.id

        response = await client.post(f"/api/v1/automation/rules/{rule_id}/toggle")
        assert response.status_code == 200
        # Model defaults is_enabled=True, so first toggle → False
        assert response.json()["is_enabled"] is False

        response2 = await client.post(f"/api/v1/automation/rules/{rule_id}/toggle")
        assert response2.json()["is_enabled"] is True

    async def test_toggle_nonexistent_rule(self, client: AsyncClient):
        response = await client.post("/api/v1/automation/rules/9999/toggle")
        assert response.status_code == 404

    async def test_rule_stats(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/automation/rules/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_rules" in data

    async def test_data_isolation(self, client: AsyncClient, other_client: AsyncClient,
                                   db: AsyncSession, test_store, second_store):
        """Each user should only see their own rules."""
        from app.models.automation_rule import AutomationRule
        for sid, name in [(test_store["id"], "User1 Rule"), (second_store["id"], "User2 Rule")]:
            db.add(AutomationRule(store_id=sid, name=name, trigger_type="scheduled"))
        await db.commit()

        r1 = await client.get("/api/v1/automation/rules")
        names1 = [r["name"] for r in r1.json()["rules"]]
        assert "User1 Rule" in names1
        assert "User2 Rule" not in names1

        r2 = await other_client.get("/api/v1/automation/rules")
        names2 = [r["name"] for r in r2.json()["rules"]]
        assert "User2 Rule" in names2
        assert "User1 Rule" not in names2

    async def test_unauthorized(self, unauth_client):
        response = await unauth_client.get("/api/v1/automation/rules")
        assert response.status_code == 401
