"""Third-party API key management - users bring their own AI provider keys."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.crypto import decrypt_api_key, encrypt_api_key
from app.models.third_party_key import ThirdPartyKey
from app.models.user import User

router = APIRouter(tags=["第三方 API 密钥"])


class CreateKeyRequest(BaseModel):
    provider: str
    label: str
    api_key: str


class KeyResponse(BaseModel):
    id: int
    provider: str
    label: str
    key_prefix: str
    is_active: bool
    created_at: str

    @classmethod
    def from_orm(cls, obj: ThirdPartyKey) -> "KeyResponse":
        return cls(
            id=obj.id,
            provider=obj.provider,
            label=obj.label,
            key_prefix=obj.key_prefix,
            is_active=obj.is_active,
            created_at=obj.created_at.strftime("%Y-%m-%d %H:%M"),
        )


PROVIDERS = {
    "openai": "OpenAI",
    "claude": "Anthropic Claude",
    "deepseek": "DeepSeek",
    "qwen": "通义千问",
    "ernie": "文心一言",
}


@router.get("", summary="列出已配置的第三方密钥")
async def list_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ThirdPartyKey).where(ThirdPartyKey.user_id == current_user.id)
    )
    keys = result.scalars().all()
    return {"items": [KeyResponse.from_orm(k) for k in keys], "total": len(keys)}


@router.post("", summary="添加第三方密钥")
async def create_key(
    req: CreateKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.provider not in PROVIDERS:
        raise HTTPException(
            status_code=422,
            detail=f"不支持的服务商: {req.provider}，可选: {', '.join(PROVIDERS.keys())}",
        )
    if not req.api_key.strip():
        raise HTTPException(status_code=422, detail="API Key 不能为空")
    if not req.label.strip():
        raise HTTPException(status_code=422, detail="请填写备注名称")

    prefix = req.api_key[:12] + "..." if len(req.api_key) > 12 else req.api_key
    encrypted = encrypt_api_key(req.api_key)

    key = ThirdPartyKey(
        user_id=current_user.id,
        provider=req.provider,
        label=req.label.strip(),
        encrypted_key=encrypted,
        key_prefix=prefix,
        is_active=True,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    return KeyResponse.from_orm(key)


@router.delete("/{key_id}", summary="删除第三方密钥")
async def delete_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ThirdPartyKey).where(
            ThirdPartyKey.id == key_id, ThirdPartyKey.user_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    await db.delete(key)
    await db.commit()
    return {"detail": "密钥已删除"}


@router.post("/{key_id}/toggle", summary="启用/停用第三方密钥")
async def toggle_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ThirdPartyKey).where(
            ThirdPartyKey.id == key_id, ThirdPartyKey.user_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    key.is_active = not key.is_active
    await db.commit()
    return {
        "detail": "已启用" if key.is_active else "已停用",
        "is_active": key.is_active,
    }


@router.get("/providers", summary="获取支持的服务商列表")
async def list_providers():
    return {
        "providers": [{"id": k, "name": v} for k, v in PROVIDERS.items()],
    }
