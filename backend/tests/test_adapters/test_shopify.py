from datetime import datetime

import pytest

from app.core.adapters.shopify import ShopifyAdapter


def test_normalize_order(sample_shopify_order):
    adapter = ShopifyAdapter(api_key="key", api_secret="secret", store_url="test.myshopify.com")

    order = adapter._normalize_order(sample_shopify_order)

    assert order.platform_id == "1234567890"
    assert order.order_number == "1001"
    assert order.email == "customer@example.com"
    assert order.total_price == 129.99
    assert order.subtotal_price == 109.99
    assert order.total_discount == 20.00
    assert order.financial_status == "paid"
    assert order.fulfillment_status == "fulfilled"
    assert order.shipping_info == {"city": "Beijing", "country": "China"}
    assert len(order.line_items) == 1
    assert order.line_items[0]["title"] == "Test Product"


def test_normalize_product(sample_shopify_product):
    adapter = ShopifyAdapter(api_key="key", api_secret="secret", store_url="test.myshopify.com")

    product = adapter._normalize_product(sample_shopify_product)

    assert product.platform_id == "111"
    assert product.title == "Test Product"
    assert product.price == 54.99
    assert product.compare_at_price == 69.99
    assert product.sku == "TP-001"
    assert product.barcode == "123456789"
    assert product.category == "Electronics"
    assert "new" in (product.tags or [])
    assert "featured" in (product.tags or [])
    assert product.inventory_quantity == 25
    assert product.status == "active"


def test_normalize_customer():
    adapter = ShopifyAdapter(api_key="key", api_secret="secret", store_url="test.myshopify.com")
    raw = {
        "id": 555,
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "orders_count": 3,
        "total_spent": "299.97",
        "verified_email": True,
        "created_at": "2026-01-01T00:00:00Z",
    }

    customer = adapter._normalize_customer(raw)

    assert customer.platform_id == "555"
    assert customer.email == "test@example.com"
    assert customer.first_name == "John"
    assert customer.last_name == "Doe"
    assert customer.orders_count == 3
    assert customer.total_spent == 299.97
    assert customer.is_verified_email is True


@pytest.mark.asyncio
async def test_get_analytics_summary_with_empty_orders():
    """Test with no orders — should return zero metrics."""
    adapter = ShopifyAdapter(api_key="key", api_secret="secret", store_url="test.myshopify.com")

    summary = await adapter.get_analytics_summary(
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 1, 31),
    )

    assert summary.total_sales == 0
    assert summary.order_count == 0
    assert summary.avg_order_value == 0
