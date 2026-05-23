from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.store import Store

router = APIRouter()


@router.get("", summary="店铺列表", description="获取所有已添加的电商平台店铺")
async def list_stores(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Store))
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


@router.post("", summary="添加店铺", description="添加新的电商平台店铺（支持 Shopify、WooCommerce 等）")
async def create_store(
    name: str = Query(..., description="店铺名称"),
    platform_type: str = Query(..., description="平台类型：shopify / woocommerce"),
    store_url: str = Query(..., description="店铺域名"),
    api_key: str = Query(..., description="API 密钥"),
    api_secret: str = Query(..., description="API 密钥密码 / Access Token"),
    db: AsyncSession = Depends(get_db),
):
    store = Store(
        name=name,
        platform_type=platform_type,
        store_url=store_url,
        api_key=api_key,
        api_secret=api_secret,
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return {"id": store.id, "name": store.name, "platform_type": store.platform_type}


@router.get("/{store_id}/sync", summary="触发数据同步", description="手动触发指定店铺的数据同步（订单、商品、客户）")
async def trigger_sync(store_id: int, db: AsyncSession = Depends(get_db)):
    from tasks.sync_tasks import sync_store
    sync_store.delay(store_id)
    return {"message": f"店铺 {store_id} 同步任务已触发"}
