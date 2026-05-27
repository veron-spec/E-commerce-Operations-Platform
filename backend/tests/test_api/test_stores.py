"""API tests for store management — CRUD and data isolation."""
import pytest
from httpx import AsyncClient


class TestListStores:
    async def test_list_stores(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/stores")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "测试店铺"

    async def test_list_stores_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/stores")
        assert response.status_code == 200
        assert response.json() == []


class TestCreateStore:
    async def test_create_store(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/stores",
            params={
                "name": "新店铺",
                "platform_type": "shopify",
                "store_url": "new.myshopify.com",
                "api_key": "key123",
                "api_secret": "secret456",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新店铺"
        assert data["platform_type"] == "shopify"
        assert "id" in data

    async def test_create_store_unauthorized(self, unauth_client: AsyncClient):
        response = await unauth_client.post(
            "/api/v1/stores",
            params={
                "name": "NoAuth",
                "platform_type": "taobao",
                "store_url": "noauth",
                "api_key": "k",
                "api_secret": "s",
            },
        )
        assert response.status_code == 401


class TestDataIsolation:
    """Users should only see their own stores."""

    async def test_user_sees_only_own_stores(
        self, client: AsyncClient, other_client: AsyncClient,
        test_store, second_store,
    ):
        # First user sees their store
        response = await client.get("/api/v1/stores")
        assert response.status_code == 200
        names = [s["name"] for s in response.json()]
        assert "测试店铺" in names
        assert "他人店铺" not in names

        # Second user sees their store
        response2 = await other_client.get("/api/v1/stores")
        assert response2.status_code == 200
        names2 = [s["name"] for s in response2.json()]
        assert "他人店铺" in names2
        assert "测试店铺" not in names2
