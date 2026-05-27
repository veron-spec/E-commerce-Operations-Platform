"""Shopee Open API v2 adapter.

Connects to Shopee's partner API for order, product, and inventory sync.
You need:
1. Register as a Shopee Partner at https://partner.shopee.com
2. Get your Partner ID, Secret Key, and Shop ID
3. Configure: api_key=PartnerID, api_secret=SecretKey, store_url=ShopID

API docs: https://open.shopee.com/documents
"""
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.core.adapters.base import (
    AnalyticsSummary,
    PlatformAdapter,
    UnifiedCustomer,
    UnifiedOrder,
    UnifiedProduct,
)


class ShopeeAdapter(PlatformAdapter):
    """Shopee Open API v2 adapter.

    Maps credentials:
      api_key    → Partner ID (string)
      api_secret → Secret Key (HMAC signing key)
      store_url  → Shop ID (numeric string)
    """

    BASE_URL = "https://partner.shopeemobile.com/api/v2"

    def __init__(self, api_key: str, api_secret: str, store_url: str = ""):
        super().__init__(api_key, api_secret, store_url)
        self.shop_id = store_url  # store_url holds the Shop ID

    def _sign(self, partner_id: int, timestamp: int) -> str:
        """Generate HMAC-SHA256 signature."""
        base_string = f"{partner_id}{timestamp}"
        return hmac.new(
            self.api_secret.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _common_params(self) -> dict[str, Any]:
        timestamp = int(time.time())
        partner_id = int(self.api_key)
        return {
            "partner_id": partner_id,
            "timestamp": timestamp,
            "sign": self._sign(partner_id, timestamp),
            "shop_id": int(self.shop_id) if self.shop_id else 0,
        }

    async def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        common = self._common_params()
        if params:
            common.update(params)
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=common, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        if data.get("error"):
            raise ValueError(
                f"Shopee API error: {data.get('error')} - {data.get('message', '')}"
            )
        return data

    async def get_orders(
        self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[UnifiedOrder]:
        """Get order list via Shopee Order API v2.

        Uses /order/get_order_list with time range filter,
        then fetches full detail for each order.
        """
        params = {
            "time_range_field": "create_time",
            "time_from": int(start_date.timestamp()),
            "time_to": int(end_date.timestamp()),
            "page_size": 100,
            "page_number": 1,
        }
        data = await self._get("/order/get_order_list", params)
        order_list = data.get("response", {}).get("order_list", [])

        results = []
        for entry in order_list:
            order_sn = entry.get("order_sn")
            if not order_sn:
                continue
            detail = await self._get_order_detail(order_sn)
            if detail:
                results.append(detail)
        return results

    async def _get_order_detail(self, order_sn: str) -> UnifiedOrder | None:
        params = {"order_sn": order_sn}
        data = await self._get("/order/get_order_detail", params)
        resp = data.get("response", {})
        order = resp.get("order_list", [{}])[0] if resp.get("order_list") else None
        if not order:
            return None
        return self._normalize_order(order)

    async def get_products(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedProduct]:
        """Get product list via Shopee Product API v2."""
        params: dict[str, Any] = {
            "page_size": 100,
            "page_number": 1,
        }
        data = await self._get("/product/get_item_list", params)
        item_list = data.get("response", {}).get("item_list", [])

        results = []
        for item in item_list:
            item_id = item.get("item_id")
            if not item_id:
                continue
            detail = await self._get_product_detail(item_id)
            if detail:
                results.append(detail)
        return results

    async def _get_product_detail(self, item_id: int) -> UnifiedProduct | None:
        params = {"item_id": item_id}
        data = await self._get("/product/get_item_base_info", params)
        resp = data.get("response", {})
        item = resp.get("item_list", [{}])[0] if resp.get("item_list") else None
        if not item:
            return None
        return self._normalize_product(item)

    async def get_customers(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedCustomer]:
        """Shopee doesn't expose customer list; derive from recent orders."""
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
                    first_name=order.shipping_info.get("recipient_name", "") if order.shipping_info else "",
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
        for li in raw.get("item_list", []):
            items.append({
                "product_id": li.get("item_id"),
                "title": li.get("item_name", ""),
                "sku": li.get("item_sku", ""),
                "quantity": int(li.get("model_quantity_purchased", 0)),
                "price": li.get("model_discounted_price", "0"),
            })
        total = float(raw.get("total_amount", 0))
        shipping = float(raw.get("shipping_fee", 0))
        return UnifiedOrder(
            platform_id=raw.get("order_sn", ""),
            order_number=raw.get("order_sn", ""),
            email=raw.get("buyer_user_id", ""),
            customer_platform_id=str(raw.get("buyer_user_id", "")),
            line_items=items,
            total_price=total,
            subtotal_price=total - shipping,
            total_discount=float(raw.get("voucher_amount", 0)),
            shipping_info={
                "recipient_name": raw.get("recipient_address", {}).get("name", ""),
                "address": raw.get("recipient_address", {}).get("full_address", ""),
                "phone": raw.get("recipient_address", {}).get("phone", ""),
            },
            financial_status=raw.get("order_status", ""),
            fulfillment_status="shipped" if raw.get("shipment_number") else None,
            created_at=self._parse_ts(raw.get("create_time")),
            updated_at=self._parse_ts(raw.get("update_time")),
        )

    def _normalize_product(self, raw: dict) -> UnifiedProduct:
        price = 0.0
        if raw.get("price_info"):
            price = float(raw["price_info"][0].get("original_price", 0)) if isinstance(raw["price_info"], list) else 0
        stock = 0
        if raw.get("stock_info"):
            stock = sum(s.get("stock", 0) for s in raw["stock_info"]) if isinstance(raw["stock_info"], list) else 0
        images = [img.get("image_url", "") for img in raw.get("images", [])] if raw.get("images") else []
        return UnifiedProduct(
            platform_id=str(raw.get("item_id", "")),
            title=raw.get("item_name", ""),
            description=raw.get("description", ""),
            price=price,
            sku=raw.get("item_sku", ""),
            category=raw.get("category_name", ""),
            tags=[raw.get("category_name", "")] if raw.get("category_name") else [],
            images=images,
            status="active" if raw.get("status") == "NORMAL" else "inactive",
            inventory_quantity=stock,
            created_at=self._parse_ts(raw.get("create_time")),
            updated_at=self._parse_ts(raw.get("update_time")),
        )

    @staticmethod
    def _parse_ts(value: int | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromtimestamp(value)
        except (ValueError, TypeError, OSError):
            return None
