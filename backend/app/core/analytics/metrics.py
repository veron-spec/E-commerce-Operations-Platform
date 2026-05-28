"""Metric definitions and calculation helpers."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SalesMetrics:
    total_revenue: float = 0.0
    order_count: int = 0
    avg_order_value: float = 0.0
    total_discount: float = 0.0
    refund_amount: float = 0.0
    refund_rate: float = 0.0
    revenue_by_day: list[dict] = field(default_factory=list)
    revenue_by_week: list[dict] = field(default_factory=list)
    revenue_by_month: list[dict] = field(default_factory=list)


@dataclass
class InventoryMetrics:
    total_products: int = 0
    total_stock_quantity: int = 0
    low_stock_count: int = 0
    out_of_stock_count: int = 0
    overstock_count: int = 0
    low_stock_items: list[dict] = field(default_factory=list)
    category_distribution: list[dict] = field(default_factory=list)


@dataclass
class TrendMetrics:
    current_period_revenue: float = 0.0
    previous_period_revenue: float = 0.0
    revenue_growth_pct: float = 0.0
    current_period_orders: int = 0
    previous_period_orders: int = 0
    order_growth_pct: float = 0.0
    daily_revenue: list[dict] = field(default_factory=list)
