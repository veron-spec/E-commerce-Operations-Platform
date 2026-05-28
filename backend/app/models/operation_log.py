from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="create/update/delete/login/register/export")
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="store/order/automation_rule/...")
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
