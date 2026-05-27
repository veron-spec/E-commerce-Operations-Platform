from app.core.adapters.base import PlatformAdapter
from app.core.adapters.lazada import LazadaAdapter
from app.core.adapters.shopee import ShopeeAdapter
from app.core.adapters.shopify import ShopifyAdapter
from app.core.adapters.taobao import TaobaoAdapter
from app.core.adapters.woocommerce import WooCommerceAdapter


def adapter_factory(platform_type: str, api_key: str, api_secret: str, store_url: str) -> PlatformAdapter:
    """Create the appropriate platform adapter based on platform_type.

    Args:
        platform_type: One of "shopify", "woocommerce", "taobao", etc.
        api_key: Platform API key / consumer key
        api_secret: Platform API secret / consumer secret
        store_url: Store URL

    Returns:
        An instance of a PlatformAdapter subclass

    Raises:
        ValueError: If platform_type is not supported
    """
    adapters = {
        "shopify": ShopifyAdapter,
        "woocommerce": WooCommerceAdapter,
        "taobao": TaobaoAdapter,
        "shopee": ShopeeAdapter,
        "lazada": LazadaAdapter,
    }

    if platform_type not in adapters:
        raise ValueError(
            f"Unsupported platform type: '{platform_type}'. "
            f"Supported types: {list(adapters.keys())}"
        )

    return adapters[platform_type](api_key=api_key, api_secret=api_secret, store_url=store_url)
