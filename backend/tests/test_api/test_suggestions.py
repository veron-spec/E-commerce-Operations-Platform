"""API tests for operational suggestions — list, generate, stats, isolation."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestSuggestions:
    async def test_list_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_list_with_store(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/suggestions")
        assert response.status_code == 200

    async def test_generate_suggestions(self, client: AsyncClient, test_store):
        response = await client.post(
            "/api/v1/suggestions/generate",
            params={"store_id": test_store["id"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "generated" in data
        assert "items" in data

    async def test_generate_wrong_store(self, client: AsyncClient, second_store):
        response = await client.post(
            "/api/v1/suggestions/generate",
            params={"store_id": second_store["id"]},
        )
        assert response.status_code == 404

    async def test_get_suggestion(self, client: AsyncClient, test_store):
        gen = await client.post(
            "/api/v1/suggestions/generate",
            params={"store_id": test_store["id"]},
        )
        items = gen.json()["items"]
        if not items:
            pytest.skip("No suggestions generated")
        sid = items[0]["id"]

        response = await client.get(f"/api/v1/suggestions/{sid}")
        assert response.status_code == 200
        assert response.json()["id"] == sid

    async def test_get_suggestion_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/suggestions/9999")
        assert response.status_code == 404

    async def test_get_suggestion_other_user(self, client: AsyncClient, other_client: AsyncClient,
                                              db: AsyncSession, second_store):
        """User A should not access User B's suggestions."""
        from app.models.suggestion import Suggestion
        s = Suggestion(
            store_id=second_store["id"],
            suggestion_type="restock",
            title="Other's suggestion",
            description="secret",
            priority="medium",
            data_source="manual",
        )
        db.add(s)
        await db.commit()
        sid = s.id

        response = await client.get(f"/api/v1/suggestions/{sid}")
        assert response.status_code == 404

    async def test_apply_suggestion(self, client: AsyncClient, db: AsyncSession, test_store):
        from app.models.suggestion import Suggestion
        s = Suggestion(
            store_id=test_store["id"],
            suggestion_type="restock",
            title="Test Apply",
            description="test",
            priority="medium",
            data_source="manual",
            status="pending",
        )
        db.add(s)
        await db.commit()
        sid = s.id

        response = await client.post(f"/api/v1/suggestions/{sid}/apply")
        assert response.status_code == 200
        assert response.json()["status"] == "applied"

    async def test_dismiss_suggestion(self, client: AsyncClient, db: AsyncSession, test_store):
        from app.models.suggestion import Suggestion
        s = Suggestion(
            store_id=test_store["id"],
            suggestion_type="restock",
            title="Test Dismiss",
            description="test",
            priority="medium",
            data_source="manual",
            status="pending",
        )
        db.add(s)
        await db.commit()
        sid = s.id

        response = await client.post(f"/api/v1/suggestions/{sid}/dismiss")
        assert response.status_code == 200
        assert response.json()["status"] == "dismissed"

    async def test_stats(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/suggestions/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_type" in data

    async def test_data_isolation(self, client: AsyncClient, other_client: AsyncClient,
                                   db: AsyncSession, test_store, second_store):
        """Each user only sees their own suggestion stats."""
        from app.models.suggestion import Suggestion
        for sid, stype in [(test_store["id"], "restock"), (second_store["id"], "marketing_campaign")]:
            db.add(Suggestion(
                store_id=sid,
                suggestion_type=stype,
                title=f"Stats {stype}",
                description="test",
                priority="medium",
                data_source="manual",
            ))
        await db.commit()

        r1 = await client.get("/api/v1/suggestions")
        types1 = [s["suggestion_type"] for s in r1.json()["items"]]
        assert "restock" in types1
        assert "marketing_campaign" not in types1

        r2 = await other_client.get("/api/v1/suggestions")
        types2 = [s["suggestion_type"] for s in r2.json()["items"]]
        assert "marketing_campaign" in types2
        assert "restock" not in types2
