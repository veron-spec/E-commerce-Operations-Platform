"""淘宝开放平台 (TOP API) 适配器。

对接淘宝的订单、商品、库存等数据。
用户需要：
1. 在 https://open.taobao.com 注册开发者并创建应用
2. 获取 App Key 和 App Secret
3. 通过 OAuth 授权获取 Session Key

TOP API 文档：https://open.taobao.com/doc.htm
"""
import hashlib
import hmac
import json
import time
import urllib.parse
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


class TaobaoAdapter(PlatformAdapter):
    """淘宝开放平台适配器。

    store_url 参数存的是你的淘宝卖家昵称（taobao_nick），
    api_key 存 App Key，
    api_secret 存 App Secret。
    Session Key 通过额外的 session_key 配置传入。
    """

    GATEWAY = "https://gw.api.taobao.com/router/rest"

    # 淘宝 API 命名映射
    API_METHODS = {
        "orders_get": "taobao.trades.sold.get",
        "products_get": "taobao.items.onsale.get",
        "inventory_get": "taobao.item.seller.get",
        "trade_get": "taobao.trade.fullinfo.get",
    }

    def __init__(self, api_key: str, api_secret: str, store_url: str = ""):
        super().__init__(api_key, api_secret, store_url)
        self.session_key = ""  # 通过 set_session_key 设置

    def set_session_key(self, session_key: str):
        """设置授权后的 Session Key。

        获取方式：
        1. 浏览器访问（替换你的 App Key）：
           https://oauth.taobao.com/authorize?response_type=code&client_id=你的AppKey&redirect_uri=urn:ietf:wg:oauth:2.0:oob
        2. 授权后得到 code
        3. 用 code 换取 token（或直接将 code 传进来，由适配器自动处理）
        """
        self.session_key = session_key

    def _sign(self, params: dict[str, str]) -> str:
        """淘宝 API 签名算法 (MD5)。"""
        sorted_params = sorted(params.items())
        sign_str = self.api_secret + "".join(f"{k}{v}" for k, v in sorted_params) + self.api_secret
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    def _build_params(self, method: str, api_params: dict | None = None) -> dict[str, str]:
        """构建请求参数并进行签名。"""
        params = {
            "method": method,
            "app_key": self.api_key,
            "session": self.session_key,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5",
            "simplify": "true",
        }
        if api_params:
            params.update(api_params)
        params["sign"] = self._sign(params)
        return params

    async def _call_api(self, method: str, api_params: dict | None = None) -> dict[str, Any]:
        """调用淘宝 TOP API。"""
        params = self._build_params(method, api_params)
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.GATEWAY, data=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

        # 淘宝 API 错误检查
        error_response = data.get("error_response")
        if error_response:
            code = error_response.get("code", "")
            msg = error_response.get("msg", "")
            sub_msg = error_response.get("sub_msg", "")
            raise ValueError(f"淘宝 API 错误 [{code}]: {msg} - {sub_msg}")

        return data

    async def get_orders(
        self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[UnifiedOrder]:
        """获取订单列表。

        淘宝 API: taobao.trades.sold.get
        文档: https://open.taobao.com/api.htm?docId=46&docType=2
        """
        params = {
            "fields": "tid,tid_str,status,payment,post_fee,total_fee,pay_time,end_time,"
                     "buyer_nick,buyer_message,receiver_name,receiver_city,receiver_state,"
                     "receiver_district,receiver_address,receiver_zip,receiver_mobile,receiver_phone,"
                     "orders.title,orders.price,orders.num,orders.oid,orders.sku_id,orders.sku_properties_name,"
                     "orders.pic_path,orders.item_meal_name,orders.seller_nick,orders.refund_status,"
                     "orders.outer_iid,orders.outer_sku_id,orders.total_fee,orders.payment,orders.discount_fee,"
                     "orders.num_iid,orders.item_type",
            "start_created": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_created": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "page_no": "1",
            "page_size": "100",
            "use_has_next": "true",
        }
        data = await self._call_api(self.API_METHODS["orders_get"], params)
        trades = data.get("trades_sold_get_response", {}).get("trades", {}).get("trade", [])

        results = []
        for raw in trades:
            unified = self._normalize_order(raw)
            if unified:
                results.append(unified)
        return results

    async def get_products(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedProduct]:
        """获取在售商品列表。

        淘宝 API: taobao.items.onsale.get
        文档: https://open.taobao.com/api.htm?docId=39&docType=2
        """
        params = {
            "fields": "num_iid,title,price,num,props_name,"
                     "pic_url,outer_id,created,modified,delist_time,"
                     "approve_status,product_id,volume,sku",
            "page_no": "1",
            "page_size": "100",
            "use_has_next": "true",
        }
        if updated_since:
            params["modified_time"] = updated_since.strftime("%Y-%m-%d %H:%M:%S")

        data = await self._call_api(self.API_METHODS["products_get"], params)
        items = data.get("items_onsale_get_response", {}).get("items", {}).get("item", [])

        results = []
        for raw in items:
            unified = self._normalize_product(raw)
            if unified:
                results.append(unified)
        return results

    async def get_customers(
        self, updated_since: datetime | None = None
    ) -> list[UnifiedCustomer]:
        """淘宝没有专门的客户列表 API，通过订单中的买家信息获取。

        注意：淘宝对买家信息有隐私保护，只能获取近期的买家信息。
        """
        end = datetime.now()
        start = end - timedelta(days=90 if not updated_since else (end - updated_since).days)
        orders = await self.get_orders(start, end)

        seen = {}
        results = []
        for order in orders:
            key = order.customer_platform_id or order.email
            if key and key not in seen:
                seen[key] = True
                results.append(UnifiedCustomer(
                    platform_id=order.customer_platform_id or "",
                    email=order.email,
                    first_name=order.shipping_info.get("receiver_name", "")[:10] if order.shipping_info else "",
                    orders_count=1,
                ))
        return results

    async def get_inventory_levels(self) -> list[dict]:
        """获取商品库存。"""
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

    def _normalize_order(self, raw: dict) -> UnifiedOrder | None:
        tid = raw.get("tid") or raw.get("tid_str")
        if not tid:
            return None

        items = []
        order_list = raw.get("orders", {}).get("order", [])
        if not isinstance(order_list, list):
            order_list = [order_list] if order_list else []

        for o in order_list:
            items.append({
                "product_id": o.get("num_iid"),
                "title": o.get("title", ""),
                "sku": o.get("outer_sku_id", ""),
                "quantity": int(o.get("num", 0)),
                "price": o.get("price", "0"),
            })

        total_price = float(raw.get("payment", 0))
        total_fee = float(raw.get("total_fee", 0))
        discount = total_fee - total_price if total_fee > total_price else 0

        return UnifiedOrder(
            platform_id=str(tid),
            order_number=str(tid),
            customer_platform_id=raw.get("buyer_nick", ""),
            email="",  # 淘宝不直接提供买家邮箱
            line_items=items,
            total_price=total_price,
            subtotal_price=total_fee,
            total_discount=discount,
            shipping_info={
                "receiver_name": raw.get("receiver_name", ""),
                "receiver_city": raw.get("receiver_city", ""),
                "receiver_state": raw.get("receiver_state", ""),
                "receiver_district": raw.get("receiver_district", ""),
                "receiver_address": raw.get("receiver_address", ""),
            },
            financial_status=raw.get("status", ""),
            created_at=self._parse_dt(raw.get("pay_time")),
        )

    def _normalize_product(self, raw: dict) -> UnifiedProduct | None:
        num_iid = raw.get("num_iid")
        if not num_iid:
            return None

        # 处理 SKU
        sku_list = raw.get("sku", {}).get("sku", [])
        if not isinstance(sku_list, list):
            sku_list = [sku_list] if sku_list else []

        total_stock = int(raw.get("num", 0))

        # 从 SKU 中获取库存总和，如果有 SKU 的话
        if sku_list:
            total_stock = sum(int(s.get("quantity", 0)) for s in sku_list)

        # 获取第一个 SKU 的外部编码
        outer_id = raw.get("outer_id", "")
        if not outer_id and sku_list:
            outer_id = sku_list[0].get("outer_id", "")

        # 解析属性名为分类
        props = raw.get("props_name", "")
        category = props.split(";")[0] if props and ";" in props else ""

        images = []
        pic_url = raw.get("pic_url", "")
        if pic_url:
            images = [pic_url]

        return UnifiedProduct(
            platform_id=str(num_iid),
            title=raw.get("title", ""),
            description="",
            price=float(raw.get("price", 0)),
            sku=outer_id,
            category=category,
            tags=[],
            images=images,
            status="active",
            inventory_quantity=total_stock,
            created_at=self._parse_dt(raw.get("created")),
            updated_at=self._parse_dt(raw.get("modified")),
        )

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            try:
                return datetime.fromisoformat(str(value).replace("Z", "+00:00").replace("T", " "))
            except (ValueError, TypeError):
                return None
