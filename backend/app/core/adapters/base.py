from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class UnifiedOrder:
    platform_id: str
    order_number: str
    customer_platform_id: str | None = None
    email: str | None = None
    line_items: list[dict] = field(default_factory=list)
    total_price: float = 0.0
    subtotal_price: float = 0.0
    total_discount: float = 0.0
    shipping_info: dict | None = None
    financial_status: str | None = None
    fulfillment_status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class UnifiedProduct:
    platform_id: str
    title: str
    description: str | None = None
    price: float = 0.0
    compare_at_price: float | None = None
    sku: str | None = None
    barcode: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    images: list[str] | None = None
    status: str = "active"
    inventory_quantity: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class UnifiedCustomer:
    platform_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    orders_count: int = 0
    total_spent: float = 0.0
    is_verified_email: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class AnalyticsSummary:
    total_sales: float = 0.0
    order_count: int = 0
    avg_order_value: float = 0.0
    total_products: int = 0
    total_customers: int = 0
    period_start: datetime | None = None
    period_end: datetime | None = None


class PlatformAdapter(ABC):
    """Abstract base class for all e-commerce platform adapters.

    Each adapter translates a specific platform's API into unified data models.
    """

    def __init__(self, api_key: str, api_secret: str, store_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.store_url = store_url.rstrip("/")

    @abstractmethod
    async def get_orders(
        self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[UnifiedOrder]:
        ...

    @abstractmethod
    async def get_products(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedProduct]:
        ...

    @abstractmethod
    async def get_customers(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedCustomer]:
        ...

    @abstractmethod
    async def get_inventory_levels(self) -> list[dict]:
        ...

    @abstractmethod
    async def get_analytics_summary(
        self, start_date: datetime, end_date: datetime
    ) -> AnalyticsSummary:
        ...
