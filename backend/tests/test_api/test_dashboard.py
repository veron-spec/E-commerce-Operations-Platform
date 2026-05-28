"""API tests for dashboard — user-scoped stats."""
from httpx import AsyncClient


class TestDashboard:
    async def test_dashboard_with_data(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "order_count" in data

    async def test_dashboard_empty_sales(self, client: AsyncClient, test_store):
        """Dashboard should return zero sales when there are no orders."""
        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        assert response.json()["total_sales"] == 0

    async def test_dashboard_unauthorized(self, unauth_client):
        response = await unauth_client.get("/api/v1/dashboard/summary")
        assert response.status_code == 401
