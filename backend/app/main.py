import json
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

# Jinja2 templates for error pages
_error_env = Environment(loader=FileSystemLoader("app/templates"), cache_size=0)
_error_templates = Jinja2Templates(env=_error_env)

from app.api.v1 import router as api_router
from app.api.v1.pages import router as pages_router
from app.config import settings
from app.core.i18n import detect_lang, get_translator
from app.core.i18n_data import translate_data
from app.models import *  # noqa: F401, F403 — register all models for Base metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"启动 {settings.app_name}")
    # 检查是否仍在使用默认密钥
    if settings.secret_key == "change-me":
        logger.warning("安全警告: SECRET_KEY 仍为默认值，请在 .env 中修改")
    if settings.encryption_key == "change-me":
        logger.warning("安全警告: ENCRYPTION_KEY 仍为默认值，请在 .env 中修改")
    # 启动时自动建表和填充种子数据
    try:
        from app.infrastructure.database import engine, Base
        # Models already imported at module level
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表已就绪")
        from app.seed_data import seed
        await seed()
    except Exception as e:
        logger.warning(f"数据库初始化异常（首次启动可忽略）: {e}")
    yield
    logger.info("服务关闭")


app = FastAPI(
    title="电商运营自动化平台",
    description="多平台电商数据同步、分析报表与自动化运营管理接口",
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.root_path,
)


# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# === 安全响应头中间件 ===
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# === 全局异常处理器 ===
def _is_browser_request(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept


def _i18n_context(request: Request) -> dict:
    """Return i18n template context for error pages."""
    cookie_lang = request.cookies.get("lang", "")
    accept_lang = request.headers.get("accept-language", "")
    lang = detect_lang(accept_lang, cookie_lang)
    return {"_": get_translator(lang), "current_lang": lang, "root_path": settings.root_path}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if _is_browser_request(request):
        template_map = {404: "errors/404.html", 403: "errors/403.html"}
        template = template_map.get(exc.status_code, "errors/500.html")
        ctx = _i18n_context(request)
        return HTMLResponse(
            content=_error_templates.get_template(template).render(ctx),
            status_code=exc.status_code,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未捕获异常: {exc} | {request.method} {request.url}")
    if _is_browser_request(request):
        ctx = _i18n_context(request)
        return HTMLResponse(
            content=_error_templates.get_template("errors/500.html").render(ctx),
            status_code=500,
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试", "status_code": 500},
    )


# === 语言检测中间件（注入 request.state 供 API 路由使用） ===
@app.middleware("http")
async def i18n_middleware(request: Request, call_next):
    cookie_lang = request.cookies.get("lang", "")
    accept_lang = request.headers.get("accept-language", "")
    lang = detect_lang(accept_lang, cookie_lang)
    request.state.lang = lang
    request.state._ = get_translator(lang)
    return await call_next(request)


# === API 响应数据翻译中间件（自动翻译 JSON 响应中的中文字段） ===
@app.middleware("http")
async def translate_api_response(request: Request, call_next):
    response = await call_next(request)

    # 只翻译 API 的 JSON 成功响应
    if (request.url.path.startswith("/api/v1/")
            and response.status_code == 200
            and "application/json" in response.headers.get("content-type", "")):

        _ = getattr(request.state, '_', None)
        if _ is None:
            return response

        try:
            # Consume the streaming body (Starlette 0.38 uses _StreamingResponse)
            body_parts = []
            async for chunk in response.body_iterator:
                body_parts.append(chunk)
            body = b"".join(body_parts)
            if not body:
                return response
            data = json.loads(body)
            translated = translate_data(data, _)
            # Strip Content-Length — the translated body has different size
            headers = dict(response.headers)
            headers.pop("content-length", None)
            return Response(
                content=json.dumps(translated, ensure_ascii=False),
                media_type="application/json",
                status_code=response.status_code,
                headers=headers,
            )
        except (json.JSONDecodeError, UnicodeDecodeError, RuntimeError, AttributeError):
            pass

    return response


# === 请求体大小限制 + 请求日志 ===
@app.middleware("http")
async def request_size_log(request: Request, call_next):
    # 请求体大小限制
    if request.method in ("POST", "PUT"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size_mb * 1024 * 1024:
            return JSONResponse(
                status_code=413,
                content={"detail": f"请求体过大，最大 {settings.max_request_size_mb}MB"},
            )
    start = time.time()
    response = await call_next(request)
    elapsed = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
    return response


app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router, prefix="/api/v1")
app.include_router(pages_router)


@app.get("/health", summary="健康检查", description="检查服务运行状态")
async def health():
    return {"status": "ok", "message": "服务运行正常"}
