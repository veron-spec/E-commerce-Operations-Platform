# Platform Adapter Development Guide

## Overview

Platform Adapters are the bridge between the e-commerce operations platform and various e-commerce backends (Shopify, WooCommerce, Magento, etc.). Each adapter implements the `PlatformAdapter` abstract base class to provide a unified interface.

## Architecture

```
[Core Application] → [Adapter Factory] → [ShopifyAdapter]
                                       → [WooCommerceAdapter]
                                       → [Custom Adapter]
```

## How to Add a New Platform

### 1. Create the adapter class

Create a new file in `app/core/adapters/{platform}.py`:

```python
from app.core.adapters.base import (
    PlatformAdapter, UnifiedOrder, UnifiedProduct,
    UnifiedCustomer, AnalyticsSummary,
)


class CustomAdapter(PlatformAdapter):
    """Adapter for Custom Platform."""

    async def get_orders(self, start_date, end_date, **kwargs) -> list[UnifiedOrder]:
        # Call platform API, translate responses
        ...

    async def get_products(self, updated_since=None) -> list[UnifiedProduct]:
        ...
```

### 2. Register in the factory

Add your adapter to `app/core/adapters/factory.py`:

```python
adapters = {
    "shopify": ShopifyAdapter,
    "custom": CustomAdapter,  # 👈 Add here
}
```

### 3. Write tests

Create `tests/test_adapters/test_{platform}.py` with normalization tests.

## API Rate Limiting

Adapters should implement rate limiting internally. Consider using the `tenacity` library for retry with exponential backoff.

## Error Handling

- Raise `httpx.HTTPStatusError` for API errors (caught by sync orchestrator)
- Network errors: the Celery task auto-retries with backoff (configurable in `sync_tasks.py`)
