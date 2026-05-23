from fastapi import APIRouter

from app.api.v1 import stores, dashboard, analytics, orders, automation
from app.api.v1 import product_selections, auto_reply, suggestions, retrospectives

router = APIRouter()
router.include_router(stores.router, prefix="/stores", tags=["店铺管理"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["数据看板"])
router.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])
router.include_router(orders.router, prefix="/orders", tags=["订单管理"])
router.include_router(automation.router, prefix="/automation", tags=["自动化规则"])
router.include_router(product_selections.router, prefix="/product-selections", tags=["捕获选品"])
router.include_router(auto_reply.router, prefix="/auto-reply", tags=["自动化客服"])
router.include_router(suggestions.router, prefix="/suggestions", tags=["运营建议"])
router.include_router(retrospectives.router, prefix="/retrospectives", tags=["复盘分析"])
