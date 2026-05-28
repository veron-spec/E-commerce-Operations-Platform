"""鎹曡幏閫夊搧 API - 閫夊搧鍒楄〃銆佸垱寤恒€佹壂鎻忋€佺粺璁°€?""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_user_store_ids, verify_store_access
from app.models.product_selection import ProductSelection

try:
    from app.pro.product_selection.service import ProductSelectionService
except ImportError:
    ProductSelectionService = Nonefrom app.models.user import User

router = APIRouter()


class CreateSelectionRequest(BaseModel):
    store_id: int
    title: str
    platform: str = "taobao"
    source: str = "manual"
    category: str | None = None
    price: float = 0
    sales_volume: int = 0
    growth_rate: float = 0
    margin: float = 0
    selection_score: float = 0
    reason: str | None = None
    status: str = "pending"


class UpdateSelectionRequest(BaseModel):
    status: str | None = None
    selection_score: float | None = None
    reason: str | None = None
    margin: float | None = None
    growth_rate: float | None = None


async def _verify_selection_owner(selection_id: int, user: User, db: AsyncSession) -> ProductSelection:
    """Verify the selection belongs to one of user's stores."""
    result = await db.execute(select(ProductSelection).where(ProductSelection.id == selection_id))
    selection = result.scalar_one_or_none()
    if not selection:
        raise HTTPException(status_code=404, detail="閫夊搧涓嶅瓨鍦?)
    await verify_store_access(selection.store_id, user, db)
    return selection


@router.get("", summary="閫夊搧鍒楄〃")
async def list_selections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    category: str | None = Query(None),
    source: str | None = Query(None),
    score_min: float | None = Query(None, ge=0, le=100),
    score_max: float | None = Query(None, ge=0, le=100),
    sort_by: str = Query("selection_score"),
    sort_desc: bool = Query(True),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    service = ProductSelectionService(db)
    return await service.list_selections(
        page=page,
        page_size=page_size,
        status=status,
        category=category,
        source=source,
        score_min=score_min,
        score_max=score_max,
        sort_by=sort_by,
        sort_desc=sort_desc,
        store_ids=store_ids,
    )


@router.post("", summary="娣诲姞閫夊搧", status_code=201)
async def create_selection(
    req: CreateSelectionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_store_access(req.store_id, user, db)
    service = ProductSelectionService(db)
    return await service.add_selection(req.model_dump())


@router.get("/stats", summary="閫夊搧缁熻")
async def selection_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    store_ids = await get_user_store_ids(user, db)
    service = ProductSelectionService(db)
    return await service.get_selection_stats(store_ids=store_ids)


@router.post("/scan", summary="鑷姩鎵弿閫夊搧")
async def trigger_scan(
    store_id: int = Query(..., description="搴楅摵ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_store_access(store_id, user, db)
    service = ProductSelectionService(db)
    results = await service.scan_for_winners(store_id)
    return {"found": len(results), "items": results}


@router.get("/{selection_id}", summary="閫夊搧璇︽儏")
async def get_selection(
    selection_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_selection_owner(selection_id, user, db)
    service = ProductSelectionService(db)
    return await service.get_selection(selection_id)


@router.put("/{selection_id}", summary="鏇存柊閫夊搧")
async def update_selection(
    selection_id: int,
    req: UpdateSelectionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_selection_owner(selection_id, user, db)
    service = ProductSelectionService(db)
    result = await service.update_selection(selection_id, req.model_dump(exclude_none=True))
    return result


@router.delete("/{selection_id}", summary="鍒犻櫎閫夊搧", status_code=204)
async def delete_selection(
    selection_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_selection_owner(selection_id, user, db)
    service = ProductSelectionService(db)
    await service.delete_selection(selection_id)
