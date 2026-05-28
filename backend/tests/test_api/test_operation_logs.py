"""API tests for operation logs."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestOperationLogs:
    async def test_list_logs_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/operation-logs/operation-logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_register_creates_log(self, unauth_client: AsyncClient):
        """Register creates a log entry, which should appear for that user."""
        resp = await unauth_client.post("/api/v1/auth/register", json={
            "email": "logtest@example.com",
            "password": "Secure@123",
            "name": "LogTest",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get("/api/v1/operation-logs/operation-logs")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1
            actions = [item["action"] for item in data["items"]]
            assert "register" in actions

    async def test_latest_logs(self, client: AsyncClient):
        response = await client.get("/api/v1/operation-logs/operation-logs/latest")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_filter_by_action(self, client: AsyncClient):
        response = await client.get("/api/v1/operation-logs/operation-logs?action=login")
        assert response.status_code == 200
        data = response.json()
        assert all(item["action"] == "login" for item in data["items"])

    async def test_unauthorized(self, unauth_client: AsyncClient):
        response = await unauth_client.get("/api/v1/operation-logs/operation-logs")
        assert response.status_code == 401
