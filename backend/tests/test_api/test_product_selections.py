"""API tests for product selections — CRUD, scan, stats, isolation."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestProductSelections:
    async def test_list_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/product-selections")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_create_selection(self, client: AsyncClient, test_store):
        response = await client.post("/api/v1/product-selections", json={
            "store_id": test_store["id"],
            "title": "热门商品",
            "platform": "taobao",
            "price": 199.0,
            "sales_volume": 5000,
            "selection_score": 85.5,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "热门商品"
        assert data["selection_score"] == 85.5

    async def test_create_selection_wrong_store(self, client: AsyncClient, second_store):
        response = await client.post("/api/v1/product-selections", json={
            "store_id": second_store["id"],
            "title": "越权选品",
            "price": 100,
        })
        assert response.status_code == 404

    async def test_get_selection(self, client: AsyncClient, test_store):
        create = await client.post("/api/v1/product-selections", json={
            "store_id": test_store["id"],
            "title": "Get Test",
            "price": 99,
        })
        sid = create.json()["id"]

        response = await client.get(f"/api/v1/product-selections/{sid}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get Test"

    async def test_get_selection_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/product-selections/9999")
        assert response.status_code == 404

    async def test_get_selection_other_user(
        self, client: AsyncClient, other_client: AsyncClient,
        db: AsyncSession, second_store,
    ):
        """User A should not see User B's selections."""
        from app.models.product_selection import ProductSelection
        s = ProductSelection(
            store_id=second_store["id"],
            title="Other's Selection",
            price=100,
            platform="taobao",
            source="manual",
        )
        db.add(s)
        await db.commit()
        sid = s.id

        response = await client.get(f"/api/v1/product-selections/{sid}")
        assert response.status_code == 404

    async def test_update_selection(self, client: AsyncClient, test_store):
        create = await client.post("/api/v1/product-selections", json={
            "store_id": test_store["id"],
            "title": "Before Update",
            "price": 100,
            "selection_score": 50,
        })
        sid = create.json()["id"]

        response = await client.put(f"/api/v1/product-selections/{sid}", json={
            "selection_score": 95.0,
            "reason": "销量增长显著",
        })
        assert response.status_code == 200
        assert response.json()["selection_score"] == 95.0
        assert response.json()["reason"] == "销量增长显著"

    async def test_delete_selection(self, client: AsyncClient, test_store):
        create = await client.post("/api/v1/product-selections", json={
            "store_id": test_store["id"],
            "title": "Delete Me",
            "price": 50,
        })
        sid = create.json()["id"]

        response = await client.delete(f"/api/v1/product-selections/{sid}")
        assert response.status_code == 204

        get_resp = await client.get(f"/api/v1/product-selections/{sid}")
        assert get_resp.status_code == 404

    async def test_scan(self, client: AsyncClient, test_store):
        response = await client.post(
            "/api/v1/product-selections/scan",
            params={"store_id": test_store["id"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "found" in data

    async def test_scan_wrong_store(self, client: AsyncClient, second_store):
        response = await client.post(
            "/api/v1/product-selections/scan",
            params={"store_id": second_store["id"]},
        )
        assert response.status_code == 404

    async def test_stats(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/product-selections/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data

    async def test_data_isolation(self, client: AsyncClient, other_client: AsyncClient,
                                   db: AsyncSession, test_store, second_store):
        """Each user only sees their own selections."""
        from app.models.product_selection import ProductSelection
        for sid, title, score in [
            (test_store["id"], "User1 Product", 90),
            (second_store["id"], "User2 Product", 80),
        ]:
            db.add(ProductSelection(
                store_id=sid, title=title, price=100,
                platform="taobao", source="manual", selection_score=score,
            ))
        await db.commit()

        r1 = await client.get("/api/v1/product-selections")
        titles1 = [s["title"] for s in r1.json()["items"]]
        assert "User1 Product" in titles1
        assert "User2 Product" not in titles1

        r2 = await other_client.get("/api/v1/product-selections")
        titles2 = [s["title"] for s in r2.json()["items"]]
        assert "User2 Product" in titles2
        assert "User1 Product" not in titles2
