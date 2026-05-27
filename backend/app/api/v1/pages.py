"""页面路由 - 可视化后台管理页面。"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.auth import decode_access_token
from app.core.i18n import detect_lang, get_translator
from app.models.user import User

router = APIRouter()

# Custom env to work around Jinja2 3.1.4+ / Starlette 1.0 cache issue on Python 3.14
_custom_env = Environment(
    loader=FileSystemLoader("app/templates"),
    cache_size=0,
    auto_reload=True,
)
templates = Jinja2Templates(env=_custom_env)


def _build_context(request: Request, **extra) -> dict:
    """Build template context with i18n support injected."""
    cookie_lang = request.cookies.get("lang", "")
    accept_lang = request.headers.get("accept-language", "")
    lang = detect_lang(accept_lang, cookie_lang)
    _ = get_translator(lang)
    return {
        "_": _,
        "current_lang": lang,
        **extra,
    }


def _get_token(request: Request) -> str | None:
    """Extract JWT from cookie or Authorization header."""
    token = request.cookies.get("token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def _require_user(request: Request, db: AsyncSession) -> User | None:
    """Check auth and return user, or None if not authenticated."""
    token = _get_token(request)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    return user if user and user.is_active else None


def _protected(handler):
    """Decorator to require auth for page routes."""
    async def wrapper(request: Request, db: AsyncSession = Depends(get_db), **kwargs):
        user = await _require_user(request, db)
        if not user:
            return RedirectResponse(url="/login", status_code=303)
        return await handler(request)
    return wrapper


# === Auth pages (no auth required) ===

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    token = _get_token(request)
    if token and decode_access_token(token):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "pages/login.html", _build_context(request))


@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_page(request: Request):
    token = _get_token(request)
    if token and decode_access_token(token):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "pages/register.html", _build_context(request))


@router.get("/logout", include_in_schema=False)
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("token", path="/")
    return resp


# === Protected pages (require auth) ===

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/dashboard.html", _build_context(request, user_name=user.name))


@router.get("/orders", response_class=HTMLResponse, include_in_schema=False)
async def orders_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/orders.html", _build_context(request, user_name=user.name))


@router.get("/sales", response_class=HTMLResponse, include_in_schema=False)
async def sales_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/sales.html", _build_context(request, user_name=user.name))


@router.get("/inventory", response_class=HTMLResponse, include_in_schema=False)
async def inventory_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/inventory.html", _build_context(request, user_name=user.name))


@router.get("/stores", response_class=HTMLResponse, include_in_schema=False)
async def stores_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/stores.html", _build_context(request, user_name=user.name))


@router.get("/automation", response_class=HTMLResponse, include_in_schema=False)
async def automation_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/automation.html", _build_context(request, user_name=user.name))


@router.get("/product-selections", response_class=HTMLResponse, include_in_schema=False)
async def product_selections_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/product_selections.html", _build_context(request, user_name=user.name))


@router.get("/auto-reply", response_class=HTMLResponse, include_in_schema=False)
async def auto_reply_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/auto_reply.html", _build_context(request, user_name=user.name))


@router.get("/suggestions", response_class=HTMLResponse, include_in_schema=False)
async def suggestions_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/suggestions.html", _build_context(request, user_name=user.name))


@router.get("/retrospectives", response_class=HTMLResponse, include_in_schema=False)
async def retrospectives_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/retrospectives.html", _build_context(request, user_name=user.name))


@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def logs_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/logs.html", _build_context(request, user_name=user.name))


@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "pages/settings.html", _build_context(request, user_name=user.name))
