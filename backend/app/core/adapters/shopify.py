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


class ShopifyAdapter(PlatformAdapter):
    """Shopify REST API adapter.

    Translates Shopify API responses into unified data models.
    Supports both REST and GraphQL endpoints.
    """

    REST_API_VERSION = "2024-07"

    @property
    def _base_url(self) -> str:
        return f"https://{self.store_url}/admin/api/{self.REST_API_VERSION}"

    def _auth_header(self) -> dict:
        return {"X-Shopify-Access-Token": self.api_secret}

    async def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._auth_header(), params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()

    async def get_orders(
        self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[UnifiedOrder]:
        params = {
            "created_at_min": start_date.isoformat(),
            "created_at_max": end_date.isoformat(),
            "status": "any",
            "limit": 250,
        }
        data = await self._get("/orders.json", params)
        results = []
        for raw in data.get("orders", []):
            results.append(self._normalize_order(raw))
        return results

    async def get_products(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedProduct]:
        params: dict[str, Any] = {"limit": 250}
        if updated_since:
            params["updated_at_min"] = updated_since.isoformat()
        data = await self._get("/products.json", params)
        results = []
        for raw in data.get("products", []):
            results.append(self._normalize_product(raw))
        return results

    async def get_customers(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedCustomer]:
        params: dict[str, Any] = {"limit": 250}
        if updated_since:
            params["updated_at_min"] = updated_since.isoformat()
        data = await self._get("/customers.json", params)
        results = []
        for raw in data.get("customers", []):
            results.append(self._normalize_customer(raw))
        return results

    async def get_inventory_levels(self) -> list[dict]:
        # First get all products with their variants
        products = await self.get_products()
        levels = []
        for p in products:
            levels.append({
                "sku": p.sku,
                "product_title": p.title,
                "quantity": p.inventory_quantity,
            })
        return levels

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
                "variant_id": li.get("variant_id"),
                "title": li.get("title"),
                "sku": li.get("sku"),
                "quantity": li.get("quantity", 0),
                "price": li.get("price", "0"),
            })
        total_price = float(raw.get("total_price", 0))
        return UnifiedOrder(
            platform_id=str(raw["id"]),
            order_number=str(raw.get("order_number", "")),
            email=raw.get("email"),
            customer_platform_id=str(raw.get("customer", {}).get("id", "")) if raw.get("customer") else None,
            line_items=items,
            total_price=total_price,
            subtotal_price=float(raw.get("subtotal_price", 0)),
            total_discount=float(raw.get("total_discounts", 0)),
            shipping_info=raw.get("shipping_address"),
            financial_status=raw.get("financial_status"),
            fulfillment_status=raw.get("fulfillment_status"),
            created_at=self._parse_dt(raw.get("created_at")),
            updated_at=self._parse_dt(raw.get("updated_at")),
        )

    def _normalize_product(self, raw: dict) -> UnifiedProduct:
        variants = raw.get("variants", [{}])
        main_variant = variants[0] if variants else {}
        images = [img.get("src", "") for img in raw.get("images", [])]
        return UnifiedProduct(
            platform_id=str(raw["id"]),
            title=raw.get("title", ""),
            description=raw.get("body_html") or "",
            price=float(main_variant.get("price", 0)),
            compare_at_price=float(main_variant.get("compare_at_price", 0)) if main_variant.get("compare_at_price") else None,
            sku=main_variant.get("sku"),
            barcode=main_variant.get("barcode"),
            category=", ".join(raw.get("product_type", "").split(",")) if raw.get("product_type") else None,
            tags=raw.get("tags", "").split(", ") if raw.get("tags") else [],
            images=images,
            status=raw.get("status", "active"),
            inventory_quantity=sum(v.get("inventory_quantity", 0) for v in variants),
            created_at=self._parse_dt(raw.get("created_at")),
            updated_at=self._parse_dt(raw.get("updated_at")),
        )

    def _normalize_customer(self, raw: dict) -> UnifiedCustomer:
        return UnifiedCustomer(
            platform_id=str(raw["id"]),
            email=raw.get("email"),
            first_name=raw.get("first_name"),
            last_name=raw.get("last_name"),
            orders_count=raw.get("orders_count", 0),
            total_spent=float(raw.get("total_spent", 0)),
            is_verified_email=raw.get("verified_email", False),
            created_at=self._parse_dt(raw.get("created_at")),
            updated_at=self._parse_dt(raw.get("updated_at")),
        )

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
