"""API tests for orders — list, filter, and data isolation."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestListOrders:
    async def test_list_orders_empty(self, client: AsyncClient, test_store):
        response = await client.get("/api/v1/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []
        assert data["total"] == 0

    async def test_list_orders_unauthorized(self, unauth_client):
        response = await unauth_client.get("/api/v1/orders")
        assert response.status_code == 401


class TestOrderDataIsolation:
    async def test_user_sees_only_own_store_orders(
        self, client: AsyncClient, other_client: AsyncClient,
        db: AsyncSession, test_store, second_store,
    ):
        from app.models.order import Order
        for store_id, order_num in [(test_store["id"], "ORD-001"), (second_store["id"], "ORD-002")]:
            order = Order(
                store_id=store_id,
                platform_id=order_num,
                order_number=order_num,
                email=f"buyer@{order_num}.com",
                line_items=[{"product_id": "1", "title": "Test", "quantity": 1, "price": "100"}],
                total_price=100,
                subtotal_price=100,
                financial_status="paid",
                fulfillment_status="fulfilled",
            )
            db.add(order)
        await db.commit()

        response = await client.get("/api/v1/orders")
        numbers = [o["order_number"] for o in response.json()["orders"]]
        assert "ORD-001" in numbers
        assert "ORD-002" not in numbers

        response2 = await other_client.get("/api/v1/orders")
        numbers2 = [o["order_number"] for o in response2.json()["orders"]]
        assert "ORD-002" in numbers2
        assert "ORD-001" not in numbers2

    async def test_filter_by_status(self, client: AsyncClient, db: AsyncSession, test_store):
        from app.models.order import Order
        for status in ["paid", "refunded"]:
            db.add(Order(
                store_id=test_store["id"],
                platform_id=f"ORD-{status}",
                order_number=f"ORD-{status}",
                email="test@test.com",
                line_items=[],
                total_price=100,
                subtotal_price=100,
                financial_status=status,
            ))
        await db.commit()

        response = await client.get("/api/v1/orders", params={"status": "refunded"})
        orders = response.json()["orders"]
        assert all(o["financial_status"] == "refunded" for o in orders)
