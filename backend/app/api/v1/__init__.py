from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1 import auth, stores, dashboard, analytics, orders, automation
from app.api.v1 import product_selections, auto_reply, suggestions, retrospectives
from app.api.v1 import operation_logs, third_party_keys
from app.infrastructure.rate_limiter import RateLimiter

router = APIRouter()
# Auth routes (no login required, IP-based rate limiting on sensitive endpoints)
router.include_router(auth.router, prefix="/auth", tags=["认证"])

# Protected routes (login required + user-based rate limiting)
protected = APIRouter(dependencies=[
    Depends(get_current_user),
    Depends(RateLimiter(60, 60, key_source="user")),
])
protected.include_router(stores.router, prefix="/stores", tags=["店铺管理"])
protected.include_router(dashboard.router, prefix="/dashboard", tags=["数据看板"])
protected.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])
protected.include_router(orders.router, prefix="/orders", tags=["订单管理"])
protected.include_router(automation.router, prefix="/automation", tags=["自动化规则"])
protected.include_router(product_selections.router, prefix="/product-selections", tags=["捕获选品"])
protected.include_router(auto_reply.router, prefix="/auto-reply", tags=["自动化客服"])
protected.include_router(suggestions.router, prefix="/suggestions", tags=["运营建议"])
protected.include_router(retrospectives.router, prefix="/retrospectives", tags=["复盘分析"])
protected.include_router(operation_logs.router, prefix="/operation-logs", tags=["操作日志"])
protected.include_router(third_party_keys.router, prefix="/third-party-keys", tags=["第三方 API 密钥"])

# Mount protected routes under the main router
router.include_router(protected)
