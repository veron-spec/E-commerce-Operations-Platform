from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.v1 import router as api_router
from app.api.v1.pages import router as pages_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"启动 {settings.app_name}")
    yield
    logger.info("服务关闭")


app = FastAPI(
    title="电商运营自动化平台",
    description="多平台电商数据同步、分析报表与自动化运营管理接口",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router, prefix="/api/v1")
app.include_router(pages_router)


@app.get("/health", summary="健康检查", description="检查服务运行状态")
async def health():
    return {"status": "ok", "message": "服务运行正常"}
