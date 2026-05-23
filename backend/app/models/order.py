from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    platform_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="Platform order ID")
    order_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    customer_platform_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    line_items: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    total_price: Mapped[float] = mapped_column(Float, default=0)
    subtotal_price: Mapped[float] = mapped_column(Float, default=0)
    total_discount: Mapped[float] = mapped_column(Float, default=0)
    shipping_info: Mapped[dict[Any, Any] | None] = mapped_column(JSON, nullable=True)
    financial_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fulfillment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="orders")
