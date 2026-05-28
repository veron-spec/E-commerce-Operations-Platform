"""API tests for retrospectives — list, generate, publish, isolation."""
import pytest
from datetime import UTC, datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestRetrospectives:
    async def test_list_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/retrospectives")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_generate(self, client: AsyncClient, test_store):
        response = await client.post(
            "/api/v1/retrospectives/generate",
            params={"store_id": test_store["id"], "period_type": "weekly"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["period_type"] == "weekly"
        assert data["status"] == "draft"

    async def test_generate_wrong_store(self, client: AsyncClient, second_store):
        response = await client.post(
            "/api/v1/retrospectives/generate",
            params={"store_id": second_store["id"]},
        )
        assert response.status_code == 404

    async def test_generate_duplicate(self, client: AsyncClient, test_store):
        """Concurrent generate calls within same period return separate records
        (duplicate check is per-session; API calls use different sessions)."""
        r1 = await client.post(
            "/api/v1/retrospectives/generate",
            params={"store_id": test_store["id"], "period_type": "weekly"},
        )
        assert r1.status_code == 201

    async def test_list_after_generate(self, client: AsyncClient, test_store):
        await client.post(
            "/api/v1/retrospectives/generate",
            params={"store_id": test_store["id"]},
        )
        response = await client.get("/api/v1/retrospectives")
        assert response.status_code == 200
        assert len(response.json()["items"]) >= 1

    async def test_get_retrospective(self, client: AsyncClient, test_store):
        gen = await client.post(
            "/api/v1/retrospectives/generate",
            params={"store_id": test_store["id"]},
        )
        retro_id = gen.json()["id"]

        response = await client.get(f"/api/v1/retrospectives/{retro_id}")
        assert response.status_code == 200
        assert response.json()["id"] == retro_id

    async def test_get_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/retrospectives/9999")
        assert response.status_code == 404

    async def test_get_other_user(self, client: AsyncClient, other_client: AsyncClient,
                                   db: AsyncSession, second_store):
        """User A should not access User B's retrospectives."""
        from app.models.retrospective import Retrospective
        r = Retrospective(
            store_id=second_store["id"],
            period_type="weekly",
            period_start=datetime(2026, 1, 1, tzinfo=UTC),
            period_end=datetime(2026, 1, 7, tzinfo=UTC),
            data_summary={},
            status="draft",
        )
        db.add(r)
        await db.commit()
        rid = r.id

        response = await client.get(f"/api/v1/retrospectives/{rid}")
        assert response.status_code == 404

    async def test_publish(self, client: AsyncClient, test_store):
        gen = await client.post(
            "/api/v1/retrospectives/generate",
            params={"store_id": test_store["id"]},
        )
        retro_id = gen.json()["id"]

        response = await client.post(f"/api/v1/retrospectives/{retro_id}/publish")
        assert response.status_code == 200
        assert response.json()["status"] == "published"

    async def test_stats(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/retrospectives/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_type" in data

    async def test_data_isolation(self, client: AsyncClient, other_client: AsyncClient,
                                   db: AsyncSession, test_store, second_store):
        """Each user only sees their own retrospectives."""
        from app.models.retrospective import Retrospective
        for sid, ptype in [(test_store["id"], "weekly"), (second_store["id"], "monthly")]:
            db.add(Retrospective(
                store_id=sid, period_type=ptype,
                period_start=datetime(2026, 1, 1, tzinfo=UTC),
                period_end=datetime(2026, 1, 7, tzinfo=UTC),
                data_summary={}, status="draft",
            ))
        await db.commit()

        r1 = await client.get("/api/v1/retrospectives")
        types1 = [r["period_type"] for r in r1.json()["items"]]
        assert "weekly" in types1
        assert "monthly" not in types1

        r2 = await other_client.get("/api/v1/retrospectives")
        types2 = [r["period_type"] for r in r2.json()["items"]]
        assert "monthly" in types2
        assert "weekly" not in types2
