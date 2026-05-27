"""Lazada Open Platform API adapter.

Connects to Lazada's REST API for order, product, and inventory sync.
You need:
1. Register as a Lazada developer at https://open.lazada.com
2. Create an application to get App Key and App Secret
3. Configure: api_key=AppKey, api_secret=AppSecret, store_url=Region

Supported regions: thailand, philippines, malaysia, singapore, indonesia, vietnam

API docs: https://open.lazada.com/doc/doc.htm
"""
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.adapters.base import (
    AnalyticsSummary,
    PlatformAdapter,
    UnifiedCustomer,
    UnifiedOrder,
    UnifiedProduct,
)

# Lazada API endpoints per region
REGION_ENDPOINTS = {
    "thailand": "https://api-th.lazada.com/rest",
    "philippines": "https://api-ph.lazada.com/rest",
    "malaysia": "https://api-my.lazada.com/rest",
    "singapore": "https://api-sg.lazada.com/rest",
    "indonesia": "https://api-id.lazada.com/rest",
    "vietnam": "https://api-vn.lazada.com/rest",
}


class LazadaAdapter(PlatformAdapter):
    """Lazada Open Platform API adapter.

    Maps credentials:
      api_key    → App Key (client_id)
      api_secret → App Secret (client_secret)
      store_url  → Region identifier (e.g. "thailand", "singapore")

    If store_url is not a recognised region key, it is used as a
    custom API base URL.
    """

    def __init__(self, api_key: str, api_secret: str, store_url: str = ""):
        super().__init__(api_key, api_secret, store_url)
        self._base = REGION_ENDPOINTS.get(store_url, store_url or "https://api.lazada.com/rest")

    def _sign(self, params: dict[str, str]) -> str:
        """Lazada HMAC-SHA256 signature.

        Sorts parameters alphabetically, concatenates key=value pairs,
        prepends the secret, and HMAC-SHA256 signs.
        """
        sorted_items = sorted(params.items())
        base_string = self.api_secret + "".join(f"{k}{v}" for k, v in sorted_items)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()

    def _build_params(self, api_params: dict | None = None) -> dict[str, str]:
        params: dict[str, str] = {
            "app_key": self.api_key,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "sign_method": "sha256",
        }
        if api_params:
            params.update(api_params)
        params["sign"] = self._sign(params)
        return params

    async def _call_api(self, path: str, api_params: dict | None = None) -> dict[str, Any]:
        params = self._build_params(api_params)
        url = f"{self._base}{path}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        if data.get("code") and data["code"] != "0":
            raise ValueError(
                f"Lazada API error [{data['code']}]: {data.get('message', '')}"
            )
        return data

    async def get_orders(
        self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[UnifiedOrder]:
        """Get orders via Lazada Orders API.

        Uses /orders/get with created_after / created_before filters.
        """
        params: dict[str, str] = {
            "created_after": start_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "created_before": end_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "status": "all",
        }
        data = await self._call_api("/orders/get", params)
        orders = data.get("data", {}).get("orders", []) if data.get("data") else []
        return [self._normalize_order(o) for o in orders if o]

    async def get_products(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedProduct]:
        """Get products via Lazaza Products API."""
        params: dict[str, str] = {
            "filter": "all",
            "limit": "100",
            "offset": "0",
        }
        data = await self._call_api("/products/get", params)
        products = data.get("data", {}).get("products", []) if data.get("data") else []
        return [self._normalize_product(p) for p in products if p]

    async def get_customers(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedCustomer]:
        """Lazada doesn't expose customer list; derive from recent orders."""
        end = datetime.now()
        start = end - timedelta(days=90 if not updated_since else (end - updated_since).days)
        orders = await self.get_orders(start, end)
        seen: dict[str, bool] = {}
        results = []
        for order in orders:
            key = order.customer_platform_id or order.email
            if key and key not in seen:
                seen[key] = True
                results.append(UnifiedCustomer(
                    platform_id=order.customer_platform_id or "",
                    email=order.email or "",
                    first_name=order.shipping_info.get("customer_name", "") if order.shipping_info else "",
                    orders_count=1,
                ))
        return results

    async def get_inventory_levels(self) -> list[dict]:
        products = await self.get_products()
        return [
            {"sku": p.sku or "", "product_title": p.title, "quantity": p.inventory_quantity}
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
        for item in raw.get("order_items", []):
            item_price_raw = item.get("item_price", "0")
            item_price = (
                float(item_price_raw.get("amount", 0))
                if isinstance(item_price_raw, dict)
                else float(item_price_raw)
            )
            items.append({
                "product_id": item.get("item_id"),
                "title": item.get("item_name", ""),
                "sku": item.get("item_sku", ""),
                "quantity": int(item.get("quantity", 0)),
                "price": str(item_price),
            })
        total_price = float(raw.get("price", 0))
        return UnifiedOrder(
            platform_id=raw.get("order_id", ""),
            order_number=raw.get("order_number", raw.get("order_id", "")),
            email=raw.get("customer_email", ""),
            customer_platform_id=raw.get("customer_id", ""),
            line_items=items,
            total_price=total_price,
            subtotal_price=float(raw.get("items_price", total_price)),
            total_discount=float(raw.get("voucher", 0)),
            shipping_info={
                "customer_name": raw.get("customer_name", ""),
                "address": f"{raw.get('address_billing', {}).get('address1', '')} {raw.get('address_billing', {}).get('address2', '')}",
                "city": raw.get("address_billing", {}).get("city", ""),
                "country": raw.get("address_billing", {}).get("country", ""),
            },
            financial_status=raw.get("status", ""),
            fulfillment_status="delivered" if raw.get("status") == "delivered" else None,
            created_at=self._parse_dt(raw.get("created_at")),
            updated_at=self._parse_dt(raw.get("updated_at")),
        )

    def _normalize_product(self, raw: dict) -> UnifiedProduct:
        skus = raw.get("skus", [])
        primary_sku = skus[0] if skus else {}
        images = [img["url"] for img in raw.get("images", [])] if raw.get("images") else []
        return UnifiedProduct(
            platform_id=str(raw.get("item_id", "")),
            title=raw.get("name", raw.get("item_name", "")),
            description=raw.get("description", ""),
            price=float(primary_sku.get("price", 0)) if primary_sku else 0,
            sku=primary_sku.get("SellerSku", "") if primary_sku else "",
            category=raw.get("category_name", ""),
            tags=[],
            images=images,
            status=raw.get("status", "active"),
            inventory_quantity=int(primary_sku.get("quantity", 0)) if primary_sku else 0,
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
