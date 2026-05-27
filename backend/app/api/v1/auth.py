from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.auth import create_access_token, hash_password, validate_password_strength, verify_password
from app.core.operation_log import log_operation
from app.infrastructure.rate_limiter import RateLimiter
from app.models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register", summary="用户注册",
             dependencies=[Depends(RateLimiter(10, 60))])
async def register(req: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Password strength
    valid, msg = validate_password_strength(req.password)
    if not valid:
        raise HTTPException(status_code=422, detail=msg)
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该邮箱已注册")

    user = User(
        email=req.email,
        name=req.name,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    await db.flush()
    await log_operation(db, user.id, "register", "user", user.id, f"用户注册：{req.email}", request)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.name},
    }


@router.post("/login", summary="用户登录",
             dependencies=[Depends(RateLimiter(5, 60))])
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    await log_operation(db, user.id, "login", "user", user.id, f"用户登录：{req.email}", request)
    await db.commit()
    token = create_access_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.name},
    }


@router.get("/me", summary="当前用户信息")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
    }
