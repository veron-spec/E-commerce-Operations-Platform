"""Tests for third-party API key management."""
import pytest
from httpx import AsyncClient


class TestThirdPartyKeys:
    async def test_list_keys_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/third-party-keys")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_create_key(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/third-party-keys",
            json={"provider": "openai", "label": "我的 OpenAI", "api_key": "sk-test1234567890abcdef"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["label"] == "我的 OpenAI"
        assert data["is_active"] is True
        assert "sk-test12345..." in data["key_prefix"]
        assert data["id"] > 0

    async def test_list_keys_after_create(self, client: AsyncClient):
        await client.post(
            "/api/v1/third-party-keys",
            json={"provider": "claude", "label": "Claude Key", "api_key": "sk-ant-test123"},
        )
        response = await client.get("/api/v1/third-party-keys")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["provider"] == "claude"

    async def test_create_key_invalid_provider(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/third-party-keys",
            json={"provider": "invalid_provider", "label": "Test", "api_key": "test-key"},
        )
        assert response.status_code == 422

    async def test_create_key_empty_label(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/third-party-keys",
            json={"provider": "openai", "label": "", "api_key": "sk-test"},
        )
        assert response.status_code == 422

    async def test_toggle_key(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/third-party-keys",
            json={"provider": "deepseek", "label": "DS Key", "api_key": "sk-ds-test123"},
        )
        key_id = resp.json()["id"]

        toggle = await client.post(f"/api/v1/third-party-keys/{key_id}/toggle")
        assert toggle.status_code == 200
        assert toggle.json()["is_active"] is False

        toggle2 = await client.post(f"/api/v1/third-party-keys/{key_id}/toggle")
        assert toggle2.status_code == 200
        assert toggle2.json()["is_active"] is True

    async def test_delete_key(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/third-party-keys",
            json={"provider": "qwen", "label": "通义千问", "api_key": "sk-qwen-test"},
        )
        key_id = resp.json()["id"]

        delete = await client.delete(f"/api/v1/third-party-keys/{key_id}")
        assert delete.status_code == 200

        # Should be gone
        list_resp = await client.get("/api/v1/third-party-keys")
        assert list_resp.json()["total"] == 0

    async def test_delete_nonexistent_key(self, client: AsyncClient):
        response = await client.delete("/api/v1/third-party-keys/99999")
        assert response.status_code == 404

    async def test_toggle_nonexistent_key(self, client: AsyncClient):
        response = await client.post("/api/v1/third-party-keys/99999/toggle")
        assert response.status_code == 404

    async def test_list_providers(self, client: AsyncClient):
        response = await client.get("/api/v1/third-party-keys/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert any(p["id"] == "openai" for p in data["providers"])

    async def test_unauthorized(self, unauth_client: AsyncClient):
        response = await unauth_client.get("/api/v1/third-party-keys")
        assert response.status_code == 401

    async def test_key_data_isolation(self, client: AsyncClient, other_client: AsyncClient):
        """User A's keys should not be visible to User B."""
        await client.post(
            "/api/v1/third-party-keys",
            json={"provider": "openai", "label": "A's Key", "api_key": "sk-aaa"},
        )
        resp = await other_client.get("/api/v1/third-party-keys")
        data = resp.json()
        assert data["total"] == 0
