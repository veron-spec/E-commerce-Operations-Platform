from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1 import auth, stores, dashboard, orders, automation
from app.api.v1 import operation_logs, third_party_keys
from app.infrastructure.rate_limiter import RateLimiter

# 鈹€鈹€ Check if pro (commercial) package is available 鈹€鈹€
try:
    import app.pro  # noqa: F401
    _HAS_PRO = True
except ImportError:
    _HAS_PRO = False
router = APIRouter()
# Auth routes (no login required, IP-based rate limiting on sensitive endpoints)
router.include_router(auth.router, prefix="/auth", tags=["璁よ瘉"])

# Protected routes (login required + user-based rate limiting)
protected = APIRouter(dependencies=[
    Depends(get_current_user),
    Depends(RateLimiter(60, 60, key_source="user")),
])
protected.include_router(stores.router, prefix="/stores", tags=["搴楅摵绠＄悊"])
protected.include_router(dashboard.router, prefix="/dashboard", tags=["鏁版嵁鐪嬫澘"])
protected.include_router(orders.router, prefix="/orders", tags=["璁㈠崟绠＄悊"])
protected.include_router(automation.router, prefix="/automation", tags=["鑷姩鍖栬鍒?])
protected.include_router(operation_logs.router, prefix="/operation-logs", tags=["鎿嶄綔鏃ュ織"])
protected.include_router(third_party_keys.router, prefix="/third-party-keys", tags=["绗笁鏂?API 瀵嗛挜"])

# Pro routes 鈥?only registered when pro/ package is present
if _HAS_PRO:
    from app.api.v1 import analytics, product_selections, auto_reply
    from app.api.v1 import suggestions, retrospectives, taobao_oauth

    protected.include_router(analytics.router, prefix="/analytics", tags=["鏁版嵁鍒嗘瀽"])
    protected.include_router(product_selections.router, prefix="/product-selections", tags=["鎹曡幏閫夊搧"])
    protected.include_router(auto_reply.router, prefix="/auto-reply", tags=["鑷姩鍖栧鏈?])
    protected.include_router(suggestions.router, prefix="/suggestions", tags=["杩愯惀寤鸿"])
    protected.include_router(retrospectives.router, prefix="/retrospectives", tags=["澶嶇洏鍒嗘瀽"])
    protected.include_router(taobao_oauth.auth_protected_router, prefix="/stores", tags=["搴楅摵绠＄悊"])

# Mount protected routes under the main router
router.include_router(protected)

# Mount unprotected callbacks (e.g. Taobao OAuth) under the main router
if _HAS_PRO:
    from app.api.v1 import taobao_oauth
    router.include_router(taobao_oauth.callback_router)