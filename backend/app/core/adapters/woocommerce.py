from datetime import datetime
from typing import Any

import httpx

from app.core.adapters.base import (
    AnalyticsSummary,
    PlatformAdapter,
    UnifiedCustomer,
    UnifiedOrder,
    UnifiedProduct,
)


class WooCommerceAdapter(PlatformAdapter):
    """WooCommerce REST API adapter.

    Uses Basic Auth (consumer_key + consumer_secret) via HTTPS.
    API docs: https://woocommerce.github.io/woocommerce-rest-api-docs/
    """

    API_VERSION = "wc/v3"

    @property
    def _base_url(self) -> str:
        return f"https://{self.store_url}/wp-json/{self.API_VERSION}"

    def _auth(self) -> tuple[str, str]:
        return (self.api_key, self.api_secret)

    async def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=self._auth(), params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()

    async def get_orders(
        self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[UnifiedOrder]:
        page = 1
        all_orders: list[UnifiedOrder] = []
        while True:
            data = await self._get("/orders", {
                "after": start_date.isoformat(),
                "before": end_date.isoformat(),
                "per_page": 100,
                "page": page,
            })
            if not data:
                break
            for raw in data:
                all_orders.append(self._normalize_order(raw))
            page += 1
        return all_orders

    async def get_products(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedProduct]:
        page = 1
        all_products: list[UnifiedProduct] = []
        params: dict[str, Any] = {"per_page": 100}
        if updated_since:
            params["after"] = updated_since.isoformat()
        while True:
            data = await self._get("/products", {**params, "page": page})
            if not data:
                break
            for raw in data:
                all_products.append(self._normalize_product(raw))
            page += 1
        return all_products

    async def get_customers(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedCustomer]:
        page = 1
        all_customers: list[UnifiedCustomer] = []
        params: dict[str, Any] = {"per_page": 100}
        if updated_since:
            params["after"] = updated_since.isoformat()
        while True:
            data = await self._get("/customers", {**params, "page": page})
            if not data:
                break
            for raw in data:
                all_customers.append(self._normalize_customer(raw))
            page += 1
        return all_customers

    async def get_inventory_levels(self) -> list[dict]:
        products = await self.get_products()
        return [
            {
                "sku": p.sku or "",
                "product_title": p.title,
                "quantity": p.inventory_quantity,
            }
            for p in products
        ]

    async def get_analytics_summary(
        self, start_date: datetime, end_date: datetime
    ) -> AnalyticsSummary:
        orders = await self.get_orders(start_date, end_date)
        total_sales = sum(o.total_price for o in orders)
        order_count = len(orders)
        return AnalyticsSummary(
            total_sales=total_sales,
            order_count=order_count,
            avg_order_value=round(total_sales / order_count, 2) if order_count else 0,
            total_products=0,
            total_customers=0,
            period_start=start_date,
            period_end=end_date,
        )

    def _normalize_order(self, raw: dict) -> UnifiedOrder:
        items = []
        for li in raw.get("line_items", []):
            items.append({
                "product_id": li.get("product_id"),
                "title": li.get("name", ""),
                "sku": li.get("sku", ""),
                "quantity": li.get("quantity", 0),
                "price": li.get("price", "0"),
            })
        return UnifiedOrder(
            platform_id=str(raw["id"]),
            order_number=str(raw.get("number", raw["id"])),
            email=raw.get("billing", {}).get("email"),
            customer_platform_id=str(raw.get("customer_id", "")) if raw.get("customer_id") else None,
            line_items=items,
            total_price=float(raw.get("total", 0)),
            subtotal_price=float(raw.get("subtotal", 0)),
            total_discount=float(raw.get("discount_total", 0)),
            shipping_info=raw.get("shipping"),
            financial_status=raw.get("status"),
            fulfillment_status="fulfilled" if raw.get("date_completed") else None,
            created_at=self._parse_dt(raw.get("date_created")),
            updated_at=self._parse_dt(raw.get("date_modified")),
        )

    def _normalize_product(self, raw: dict) -> UnifiedProduct:
        images = [img.get("src", "") for img in raw.get("images", [])]
        return UnifiedProduct(
            platform_id=str(raw["id"]),
            title=raw.get("name", ""),
            description=raw.get("description", "") or "",
            price=float(raw.get("price", 0)),
            compare_at_price=float(raw["regular_price"]) if raw.get("regular_price") and float(raw["regular_price"]) != float(raw.get("price", 0)) else None,
            sku=raw.get("sku"),
            category=raw["categories"][0]["name"] if raw.get("categories") else None,
            tags=[t["name"] for t in raw.get("tags", [])],
            images=images,
            status=raw.get("status", "active"),
            inventory_quantity=raw.get("stock_quantity") or 0,
            created_at=self._parse_dt(raw.get("date_created")),
            updated_at=self._parse_dt(raw.get("date_modified")),
        )

    def _normalize_customer(self, raw: dict) -> UnifiedCustomer:
        return UnifiedCustomer(
            platform_id=str(raw["id"]),
            email=raw.get("email"),
            first_name=raw.get("first_name"),
            last_name=raw.get("last_name"),
            orders_count=raw.get("orders_count", 0),
            total_spent=float(raw.get("total_spent", 0)),
            is_verified_email=bool(raw.get("email")),
            created_at=self._parse_dt(raw.get("date_created")),
            updated_at=self._parse_dt(raw.get("date_modified")),
        )

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
