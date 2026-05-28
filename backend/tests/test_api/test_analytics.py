"""API tests for analytics endpoints — sales, inventory, trends, top products."""
import pytest
from httpx import AsyncClient


class TestSalesAnalysis:
    async def test_sales_analysis(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/analytics/sales", params={"days": 7})
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "order_count" in data

    async def test_sales_analysis_with_store(self, client: AsyncClient, test_store):
        response = await client.get(
            "/api/v1/analytics/sales",
            params={"days": 7, "store_id": test_store["id"]},
        )
        assert response.status_code == 200

    async def test_sales_analysis_unauthorized_store(self, client: AsyncClient, second_store):
        response = await client.get(
            "/api/v1/analytics/sales",
            params={"store_id": second_store["id"]},
        )
        assert response.status_code == 404


class TestInventoryAnalysis:
    async def test_inventory_analysis(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/analytics/inventory")
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data

    async def test_inventory_with_custom_threshold(self, client: AsyncClient, test_store):
        response = await client.get(
            "/api/v1/analytics/inventory",
            params={"low_stock_threshold": 5},
        )
        assert response.status_code == 200


class TestTrendAnalysis:
    async def test_trends(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/analytics/trends", params={"days": 30})
        assert response.status_code == 200
        data = response.json()
        assert "revenue_growth_pct" in data


class TestTopProducts:
    async def test_top_products(self, client: AsyncClient, test_store):
        response = await client.get(
            "/api/v1/analytics/products/top",
            params={"days": 30, "limit": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert "top_products" in data
        assert "period_days" in data


class TestAnalyticsAuth:
    async def test_unauthorized(self, unauth_client):
        response = await unauth_client.get("/api/v1/analytics/sales")
        assert response.status_code == 401

    async def test_data_isolation(self, client: AsyncClient, second_store):
        """Should not see other user's store analytics."""
        response = await client.get(
            "/api/v1/analytics/sales",
            params={"store_id": second_store["id"]},
        )
        assert response.status_code == 404
