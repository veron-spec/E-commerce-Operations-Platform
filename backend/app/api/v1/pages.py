"""页面路由 - 可视化后台管理页面。"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

router = APIRouter()

# Custom env to work around Jinja2 3.1.4+ / Starlette 1.0 cache issue on Python 3.14
_custom_env = Environment(
    loader=FileSystemLoader("app/templates"),
    cache_size=0,
    auto_reload=True,
)
templates = Jinja2Templates(env=_custom_env)


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "pages/dashboard.html")


@router.get("/orders", response_class=HTMLResponse, include_in_schema=False)
async def orders_page(request: Request):
    return templates.TemplateResponse(request, "pages/orders.html")


@router.get("/sales", response_class=HTMLResponse, include_in_schema=False)
async def sales_page(request: Request):
    return templates.TemplateResponse(request, "pages/sales.html")


@router.get("/inventory", response_class=HTMLResponse, include_in_schema=False)
async def inventory_page(request: Request):
    return templates.TemplateResponse(request, "pages/inventory.html")


@router.get("/stores", response_class=HTMLResponse, include_in_schema=False)
async def stores_page(request: Request):
    return templates.TemplateResponse(request, "pages/stores.html")


@router.get("/automation", response_class=HTMLResponse, include_in_schema=False)
async def automation_page(request: Request):
    return templates.TemplateResponse(request, "pages/automation.html")


@router.get("/product-selections", response_class=HTMLResponse, include_in_schema=False)
async def product_selections_page(request: Request):
    return templates.TemplateResponse(request, "pages/product_selections.html")


@router.get("/auto-reply", response_class=HTMLResponse, include_in_schema=False)
async def auto_reply_page(request: Request):
    return templates.TemplateResponse(request, "pages/auto_reply.html")


@router.get("/suggestions", response_class=HTMLResponse, include_in_schema=False)
async def suggestions_page(request: Request):
    return templates.TemplateResponse(request, "pages/suggestions.html")


@router.get("/retrospectives", response_class=HTMLResponse, include_in_schema=False)
async def retrospectives_page(request: Request):
    return templates.TemplateResponse(request, "pages/retrospectives.html")


@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request):
    return templates.TemplateResponse(request, "pages/settings.html")
