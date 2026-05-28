"""Two-tier cache: L1 (hot in-memory) + L2 (Redis with graceful fallback)."""
import functools
import inspect
import json
import time
from collections import OrderedDict
from typing import Any, Callable

import redis.asyncio as aioredis

from app.config import settings

_redis: aioredis.Redis | None = None

# ── L1 in-memory cache ──────────────────────────────────────────────
_l1: dict[str, tuple[Any, float]] = OrderedDict()
L1_TTL = 30          # seconds — hot data lives in memory
L1_MAX_ITEMS = 500   # max entries before LRU eviction


def _l1_get(key: str) -> Any | None:
    item = _l1.get(key)
    if item and time.monotonic() - item[1] < L1_TTL:
        return item[0]
    if item:
        del _l1[key]
    return None


def _l1_set(key: str, value: Any) -> None:
    if len(_l1) >= L1_MAX_ITEMS:
        _l1.popitem(last=False)  # LRU eviction
    _l1[key] = (value, time.monotonic())


def _l1_clear_prefix(prefix: str) -> None:
    stale = [k for k in _l1 if k.startswith(prefix)]
    for k in stale:
        del _l1[k]


# ── Redis connection ─────────────────────────────────────────────────

async def get_redis() -> aioredis.Redis | None:
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.celery_broker_url, decode_responses=True)
            await _redis.ping()
        except Exception:
            _redis = None
    return _redis


# ── Public API ───────────────────────────────────────────────────────

async def cache_get(key: str) -> Any | None:
    """Two-tier get: L1 (memory) → L2 (Redis)."""
    # L1 — fast path
    result = _l1_get(key)
    if result is not None:
        return result
    # L2 — Redis
    r = await get_redis()
    if not r:
        return None
    try:
        data = await r.get(key)
        result = json.loads(data) if data else None
        if result is not None:
            _l1_set(key, result)  # warm L1 from L2
        return result
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Two-tier set: L1 (memory) + L2 (Redis)."""
    _l1_set(key, value)
    r = await get_redis()
    if not r:
        return
    try:
        await r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


async def cache_invalidate(prefix: str) -> int:
    """Invalidate all cache entries with the given prefix across both tiers."""
    _l1_clear_prefix(prefix)
    r = await get_redis()
    if not r:
        return 0
    try:
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=f"{prefix}*", count=100)
            if keys:
                await r.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        return deleted
    except Exception:
        return 0


async def cache_stats() -> dict:
    """Current cache state for monitoring."""
    r = await get_redis()
    redis_keys = 0
    if r:
        try:
            redis_keys = await r.dbsize()
        except Exception:
            pass
    return {"l1_entries": len(_l1), "l1_max": L1_MAX_ITEMS, "redis_keys": redis_keys}


# ── TTL presets ──────────────────────────────────────────────────────

CACHE_TTL = {
    "dashboard": 120,
    "analytics": 300,
    "reports": settings.report_cache_ttl_hours * 3600,
}


# ── Decorator ────────────────────────────────────────────────────────

def cached(ttl: int, prefix: str) -> Callable:
    """Decorator: two-tier cache for async endpoint functions.

    Usage::

        @router.get(...)
        @cached(ttl=120, prefix="dashboard:summary")
        async def dashboard_summary(user: User, ..., db: AsyncSession):
            ...

    The decorator builds the cache key from the function name, module,
    and all non-excluded parameters (``db``, ``request`` are skipped
    automatically; User/Store objects use their ``.id``).
    """
    EXCLUDED = {"db", "request", "cls"}

    def make_key(func: Callable, args: tuple, kwargs: dict) -> str:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        parts = []
        for name, val in bound.arguments.items():
            if name in EXCLUDED or val is None:
                continue
            if hasattr(val, "id"):
                parts.append(f"{name}:{val.id}")
            elif isinstance(val, (str, int, float, bool)):
                parts.append(f"{name}:{val}")
        return f"{prefix}:{':'.join(parts)}"

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = make_key(func, args, kwargs)
            cached = await cache_get(key)
            if cached is not None:
                return cached
            result = await func(*args, **kwargs)
            await cache_set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
