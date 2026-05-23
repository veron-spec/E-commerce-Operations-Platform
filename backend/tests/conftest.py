import pytest


@pytest.fixture
def sample_shopify_order() -> dict:
    return {
        "id": 1234567890,
        "order_number": 1001,
        "email": "customer@example.com",
        "total_price": "129.99",
        "subtotal_price": "109.99",
        "total_discounts": "20.00",
        "financial_status": "paid",
        "fulfillment_status": "fulfilled",
        "customer": {"id": 987654321},
        "shipping_address": {"city": "Beijing", "country": "China"},
        "line_items": [
            {
                "product_id": 111,
                "variant_id": 222,
                "title": "Test Product",
                "sku": "TP-001",
                "quantity": 2,
                "price": "54.99",
            }
        ],
        "created_at": "2026-05-01T10:00:00Z",
        "updated_at": "2026-05-02T10:00:00Z",
    }


@pytest.fixture
def sample_shopify_product() -> dict:
    return {
        "id": 111,
        "title": "Test Product",
        "body_html": "<p>A test product</p>",
        "product_type": "Electronics",
        "status": "active",
        "tags": "new, featured",
        "variants": [
            {
                "price": "54.99",
                "compare_at_price": "69.99",
                "sku": "TP-001",
                "barcode": "123456789",
                "inventory_quantity": 25,
            }
        ],
        "images": [{"src": "https://example.com/image.jpg"}],
        "created_at": "2026-04-01T10:00:00Z",
        "updated_at": "2026-05-01T10:00:00Z",
    }
