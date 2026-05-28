"""Simple in-memory rate limiter with optional Redis backend."""
import time
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, status


@dataclass
class Bucket:
    tokens: float
    last_refill: float


class MemoryRateLimiter:
    """Token-bucket rate limiter per client key."""

    def __init__(self):
        self._buckets: dict[str, Bucket] = {}
        self._cleanup_interval = 300  # seconds
        self._last_cleanup = time.monotonic()

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed. Returns True if allowed, False if rate-limited."""
        now = time.monotonic()
        self._maybe_cleanup(now)

        if key not in self._buckets:
            self._buckets[key] = Bucket(tokens=max_requests - 1, last_refill=now)
            return True

        bucket = self._buckets[key]
        elapsed = now - bucket.last_refill
        # Refill tokens based on elapsed time
        refill = elapsed * (max_requests / window_seconds)
        bucket.tokens = min(max_requests, bucket.tokens + refill)
        bucket.last_refill = now

        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return True

        return False

    def _maybe_cleanup(self, now: float) -> None:
        if now - self._last_cleanup > self._cleanup_interval:
            stale = [k for k, b in self._buckets.items()
                     if now - b.last_refill > self._cleanup_interval]
            for k in stale:
                del self._buckets[k]
            self._last_cleanup = now


# Shared instance
_limiter = MemoryRateLimiter()


def check_rate_limit(key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
    """Global rate limit check."""
    return _limiter.check(key, max_requests, window_seconds)


class RateLimiter:
    """FastAPI dependency for endpoint rate limiting.

    Usage::

        # IP-based (default), 10 requests per 60 seconds
        @router.get("/path", dependencies=[Depends(RateLimiter(10, 60))])

        # User-based (requires auth dependency to run first)
        @router.get("/path", dependencies=[Depends(RateLimiter(60, 60, key_source="user"))])
    """

    def __init__(self, max_requests: int, window_seconds: int = 60, *, key_source: str = "ip"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_source = key_source  # "ip" or "user"

    async def __call__(self, request: Request) -> bool:
        from app.config import settings

        if not settings.rate_limit_enabled:
            return True

        if self.key_source == "user":
            user = getattr(request.state, "user", None) or getattr(request, "user", None)
            key = f"user:{user.id}" if user else (request.client.host if request.client else "unknown")
        else:
            key = request.client.host if request.client else "unknown"

        if not check_rate_limit(key, self.max_requests, self.window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后重试",
            )
        return True
