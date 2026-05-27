"""API tests for auto-reply rules — CRUD, match test, stats, isolation."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAutoReply:
    async def test_create_rule(self, client: AsyncClient, test_store):
        response = await client.post("/api/v1/auto-reply", json={
            "store_id": test_store["id"],
            "name": "价格询问",
            "trigger_keywords": ["价格", "多少钱"],
            "match_type": "contains",
            "reply_template": "您好，当前售价为 199 元",
            "priority": 10,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "价格询问"
        assert data["trigger_keywords"] == ["价格", "多少钱"]

    async def test_create_rule_wrong_store(self, client: AsyncClient, second_store):
        response = await client.post("/api/v1/auto-reply", json={
            "store_id": second_store["id"],
            "name": "越权规则",
            "trigger_keywords": ["x"],
            "match_type": "contains",
            "reply_template": "无权访问",
        })
        assert response.status_code == 404

    async def test_list_rules(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/auto-reply")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_list_rules_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/auto-reply")
        assert response.status_code == 200
        assert response.json()["items"] == []

    async def test_get_rule(self, client: AsyncClient, test_store):
        create_resp = await client.post("/api/v1/auto-reply", json={
            "store_id": test_store["id"],
            "name": "Get Test",
            "trigger_keywords": ["hello"],
            "match_type": "exact",
            "reply_template": "Hi there",
        })
        rule_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/auto-reply/{rule_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    async def test_get_rule_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/auto-reply/9999")
        assert response.status_code == 404

    async def test_get_rule_other_user(self, client: AsyncClient, other_client: AsyncClient, db: AsyncSession, second_store):
        """User A should not be able to view User B's rules."""
        from app.models.auto_reply import AutoReply
        rule = AutoReply(
            store_id=second_store["id"],
            name="Other's Rule",
            trigger_keywords=["secret"],
            match_type="contains",
            reply_template="secret reply",
        )
        db.add(rule)
        await db.commit()
        rule_id = rule.id

        response = await client.get(f"/api/v1/auto-reply/{rule_id}")
        assert response.status_code == 404

    async def test_update_rule(self, client: AsyncClient, test_store):
        create_resp = await client.post("/api/v1/auto-reply", json={
            "store_id": test_store["id"],
            "name": "Before Update",
            "trigger_keywords": ["old"],
            "match_type": "contains",
            "reply_template": "old reply",
        })
        rule_id = create_resp.json()["id"]

        response = await client.put(f"/api/v1/auto-reply/{rule_id}", json={
            "name": "After Update",
            "priority": 99,
        })
        assert response.status_code == 200
        assert response.json()["name"] == "After Update"
        assert response.json()["priority"] == 99

    async def test_toggle_rule(self, client: AsyncClient, test_store):
        create_resp = await client.post("/api/v1/auto-reply", json={
            "store_id": test_store["id"],
            "name": "Toggle Test",
            "trigger_keywords": ["toggle"],
            "match_type": "contains",
            "reply_template": "toggled",
        })
        rule_id = create_resp.json()["id"]

        resp = await client.post(f"/api/v1/auto-reply/{rule_id}/toggle")
        assert resp.status_code == 200
        assert resp.json()["is_enabled"] is False

        resp2 = await client.post(f"/api/v1/auto-reply/{rule_id}/toggle")
        assert resp2.json()["is_enabled"] is True

    async def test_delete_rule(self, client: AsyncClient, test_store):
        create_resp = await client.post("/api/v1/auto-reply", json={
            "store_id": test_store["id"],
            "name": "Delete Me",
            "trigger_keywords": ["del"],
            "match_type": "contains",
            "reply_template": "bye",
        })
        rule_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/auto-reply/{rule_id}")
        assert response.status_code == 204

        get_resp = await client.get(f"/api/v1/auto-reply/{rule_id}")
        assert get_resp.status_code == 404

    async def test_test_match(self, client: AsyncClient, test_store):
        await client.post("/api/v1/auto-reply", json={
            "store_id": test_store["id"],
            "name": "Price Query",
            "trigger_keywords": ["价格", "price"],
            "match_type": "contains",
            "reply_template": "价格是 199 元",
        })

        response = await client.post("/api/v1/auto-reply/test", json={
            "message": "这个价格是多少？",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is True
        assert data["reply"] == "价格是 199 元"

    async def test_test_match_no_match(self, client: AsyncClient):
        response = await client.post("/api/v1/auto-reply/test", json={
            "message": "完全无关的消息",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is False

    async def test_match_stats(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/auto-reply/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_rules" in data
        assert "enabled" in data

    async def test_data_isolation(self, client: AsyncClient, other_client: AsyncClient,
                                   db: AsyncSession, test_store, second_store):
        """Each user only sees their own auto-reply rules."""
        from app.models.auto_reply import AutoReply
        for sid, name in [(test_store["id"], "User1 Rule"), (second_store["id"], "User2 Rule")]:
            db.add(AutoReply(
                store_id=sid, name=name,
                trigger_keywords=["x"], match_type="contains", reply_template="reply",
            ))
        await db.commit()

        r1 = await client.get("/api/v1/auto-reply")
        names1 = [r["name"] for r in r1.json()["items"]]
        assert "User1 Rule" in names1
        assert "User2 Rule" not in names1

        r2 = await other_client.get("/api/v1/auto-reply")
        names2 = [r["name"] for r in r2.json()["items"]]
        assert "User2 Rule" in names2
        assert "User1 Rule" not in names2
