"""Taobao OAuth 授权流程。

流程：
  1. 前端请求 auth-url → 后端生成淘宝授权 URL → 前端跳转
  2. 卖家在淘宝页面授权 → 淘宝回调到 callback 端点
  3. 后端用 code 换取 token → 加密存储到 store 记录 → 重定向回店铺列表

注意：
  回调端点在浏览器上下文中执行（淘宝重定向），不走 API Token 认证。
  安全性由 `state` 参数中的 store_id + 服务端 code 换 token 的不可伪造性保障。
"""
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, verify_store_access
from app.config import settings
from app.core.crypto import decrypt_api_key, encrypt_api_key
from app.core.operation_log import log_operation
from app.models.store import Store
from app.models.user import User

# ── 两个路由器 ────────────────────────────────────────────────────────────────
# auth_protected_router: 需要用户登录（挂载到 protected 下）
# callback_router: 公开回调（挂载到主 router 下，淘宝重定向无 token）
auth_protected_router = APIRouter()
callback_router = APIRouter()

TAOBAO_OAUTH_AUTHORIZE_URL = "https://oauth.taobao.com/authorize"
TAOBAO_OAUTH_TOKEN_URL = "https://oauth.taobao.com/token"


@auth_protected_router.get(
    "/{store_id}/taobao/auth-url",
    summary="获取淘宝 OAuth 授权 URL",
    description="生成跳转到淘宝授权页面的 URL，state 参数中携带 store_id",
)
async def get_taobao_auth_url(
    store_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_store_access(store_id, user, db)

    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")

    if store.platform_type != "taobao":
        raise HTTPException(status_code=400, detail="仅淘宝店铺支持 OAuth 授权")

    app_key = decrypt_api_key(store.api_key)

    params = {
        "response_type": "code",
        "client_id": app_key,
        "redirect_uri": settings.taobao_redirect_uri,
        "state": str(store_id),
    }
    url = f"{TAOBAO_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    logger.info(f"生成淘宝 OAuth URL: store_id={store_id}")
    return {"auth_url": url}


@callback_router.get(
    "/auth/taobao/callback",
    summary="淘宝 OAuth 回调",
    description="淘宝授权后的回调端点，用 code 换 token 并存储",
    include_in_schema=False,
)
async def taobao_oauth_callback(
    code: str = Query(..., description="淘宝返回的授权码"),
    state: str = Query(..., description="携带的 store_id"),
    db: AsyncSession = Depends(get_db),
):
    store_id = state.strip()

    # 查找店铺
    result = await db.execute(select(Store).where(Store.id == int(store_id)))
    store = result.scalar_one_or_none()
    if not store:
        logger.error(f"淘宝 OAuth 回调：店铺不存在 store_id={store_id}")
        return RedirectResponse(url=f"/stores?taobao_auth=error&msg=店铺不存在", status_code=303)

    # 解密凭证
    try:
        app_key = decrypt_api_key(store.api_key)
        app_secret = decrypt_api_key(store.api_secret)
    except Exception as e:
        logger.error(f"解密店铺凭证失败 store_id={store_id}: {e}")
        return RedirectResponse(url=f"/stores?taobao_auth=error&msg=解密凭证失败", status_code=303)

    # 用 code 换 token
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TAOBAO_OAUTH_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": app_key,
                    "client_secret": app_secret,
                    "redirect_uri": settings.taobao_redirect_uri,
                },
                timeout=30,
            )
            resp.raise_for_status()
            token_data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"淘宝 token 换取失败 store_id={store_id}: {e.response.text}")
        return RedirectResponse(url=f"/stores?taobao_auth=error&msg=Token 换取失败", status_code=303)
    except Exception as e:
        logger.error(f"淘宝 token 换取异常 store_id={store_id}: {e}")
        return RedirectResponse(url=f"/stores?taobao_auth=error&msg=网络请求异常", status_code=303)

    error_code = token_data.get("error_code")
    if error_code:
        error_msg = token_data.get("error_message", "未知错误")
        logger.error(f"淘宝 OAuth 返回错误 store_id={store_id}: [{error_code}] {error_msg}")
        return RedirectResponse(url=f"/stores?taobao_auth=error&msg={error_msg}", status_code=303)

    access_token = token_data.get("access_token", "")
    refresh_token_val = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 86400)
    taobao_user_nick = token_data.get("taobao_user_nick", "")

    if not access_token:
        logger.error(f"淘宝 OAuth 返回空 access_token store_id={store_id}")
        return RedirectResponse(url=f"/stores?taobao_auth=error&msg=未获取到 access_token", status_code=303)

    # 加密存储
    try:
        store.session_key = encrypt_api_key(access_token)
        store.refresh_token = encrypt_api_key(refresh_token_val) if refresh_token_val else None
        store.token_expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in))
    except Exception as e:
        logger.error(f"加密 token 失败 store_id={store_id}: {e}")
        return RedirectResponse(url=f"/stores?taobao_auth=error&msg=加密存储失败", status_code=303)

    # 更新卖家昵称（如果 store_url 为空）
    if not store.store_url and taobao_user_nick:
        store.store_url = taobao_user_nick

    db.add(store)
    await log_operation(
        db, store.user_id, "update", "store", store.id,
        f"淘宝 OAuth 授权成功：{taobao_user_nick or store.name}",
        None,
    )
    await db.commit()
    await db.refresh(store)

    logger.info(f"淘宝 OAuth 授权成功 store_id={store_id}, nick={taobao_user_nick}")
    return RedirectResponse(url="/stores?taobao_auth=success", status_code=303)
