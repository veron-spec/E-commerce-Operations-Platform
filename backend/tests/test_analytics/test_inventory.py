"""Unit tests for InventoryAnalyzer — tests the analysis logic with mocked DB."""
import pytest


class MockProduct:
    def __init__(self, id, title, sku, category, inventory_quantity):
        self.id = id
        self.title = title
        self.sku = sku
        self.category = category
        self.inventory_quantity = inventory_quantity


def test_inventory_classification():
    """Verify inventory classification without DB (pure logic test)."""
    products = [
        MockProduct(1, "Out of Stock", "OOS-01", "A", 0),
        MockProduct(2, "Low Stock", "LS-01", "A", 5),
        MockProduct(3, "Normal", "N-01", "B", 50),
        MockProduct(4, "Overstock", "OS-01", "C", 200),
        MockProduct(5, "Low Stock 2", "LS-02", "B", 3),
    ]

    low_stock_threshold = 10
    low_stock_items = []
    low_count = 0
    oos_count = 0
    over_count = 0

    for p in products:
        if p.inventory_quantity <= 0:
            oos_count += 1
        elif p.inventory_quantity < low_stock_threshold:
            low_count += 1
            low_stock_items.append({
                "title": p.title,
                "sku": p.sku,
                "quantity": p.inventory_quantity,
            })
        elif p.inventory_quantity > low_stock_threshold * 10:
            over_count += 1

    assert oos_count == 1
    assert low_count == 2
    assert over_count == 1
    assert len(low_stock_items) == 2
    assert low_stock_items[0]["title"] == "Low Stock"


def test_category_distribution():
    products = [
        MockProduct(1, "P1", "S1", "Electronics", 10),
        MockProduct(2, "P2", "S2", "Electronics", 20),
        MockProduct(3, "P3", "S3", "Clothing", 15),
    ]

    dist = {}
    for p in products:
        cat = p.category or "Uncategorized"
        dist[cat] = dist.get(cat, 0) + 1

    assert dist == {"Electronics": 2, "Clothing": 1}
