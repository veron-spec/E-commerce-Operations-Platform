"""Operation logging service — audit trail for user actions."""
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation_log import OperationLog


async def log_operation(
    db: AsyncSession,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: str | int | None = None,
    detail: str | None = None,
    request: Request | None = None,
) -> OperationLog:
    """Create an operation log entry."""
    entry = OperationLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        detail=detail,
        ip_address=request.client.host if request and request.client else None,
    )
    db.add(entry)
    await db.flush()
    return entry
