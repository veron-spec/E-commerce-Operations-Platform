from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_access_token
from app.infrastructure.database import async_session
from app.models.store import Store
from app.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    authorization: str = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = None
    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    # Fall back to cookie
    if not token:
        token = request.cookies.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="请先登录")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="无效或过期的 Token")
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    request.state.user = user
    return user


async def get_user_store_ids(user: User, db: AsyncSession) -> list[int]:
    """Get all store IDs belonging to a user."""
    result = await db.execute(
        select(Store.id).where(Store.user_id == user.id)
    )
    return [row[0] for row in result.all()]


async def verify_store_access(
    store_id: int | None,
    user: User,
    db: AsyncSession,
) -> list[int]:
    """Verify store access and return scoped store IDs.

    If store_id is provided, checks it belongs to the user (raises 404 if not).
    If store_id is None, returns all user's store IDs.
    """
    user_store_ids = await get_user_store_ids(user, db)
    if not user_store_ids:
        raise HTTPException(status_code=404, detail="没有找到店铺，请先添加店铺")
    if store_id is not None and store_id not in user_store_ids:
        raise HTTPException(status_code=404, detail="店铺不存在或无权访问")
    return [store_id] if store_id is not None else user_store_ids
