from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db,
    get_user_store_ids,
    verify_store_access,
)
from app.core.operation_log import log_operation
from app.models.store import Store
from app.models.user import User

router = APIRouter()


@router.get("", summary="店铺列表", description="获取当前用户的所有店铺")
async def list_stores(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    if not store_ids:
        return []
    result = await db.execute(select(Store).where(Store.id.in_(store_ids)))
    stores = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "platform_type": s.platform_type,
            "store_url": s.store_url,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in stores
    ]


@router.post("", summary="添加店铺", description="添加新的电商平台店铺")
async def create_store(
    request: Request,
    name: str = Query(..., description="店铺名称"),
    platform_type: str = Query(..., description="平台类型：shopify / woocommerce / taobao / shopee / lazada"),
    store_url: str = Query(..., description="店铺域名"),
    api_key: str = Query(..., description="API 密钥"),
    api_secret: str = Query(..., description="API 密钥密码 / Access Token"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store = Store(
        user_id=user.id,
        name=name,
        platform_type=platform_type,
        store_url=store_url,
        api_key=api_key,
        api_secret=api_secret,
    )
    db.add(store)
    await db.flush()
    await log_operation(db, user.id, "create", "store", store.id, f"添加店铺：{name}（{platform_type}）", request)
    await db.commit()
    await db.refresh(store)
    return {"id": store.id, "name": store.name, "platform_type": store.platform_type}


@router.get("/{store_id}/sync", summary="触发数据同步", description="手动触发指定店铺的数据同步")
async def trigger_sync(
    store_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_store_access(store_id, user, db)
    from tasks.sync_tasks import sync_store
    sync_store.delay(store_id)
    return {"message": f"店铺 {store_id} 同步任务已触发"}
