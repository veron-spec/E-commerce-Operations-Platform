from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="shopify, woocommerce, etc.")
    api_key: Mapped[str] = mapped_column(Text, nullable=False, comment="Encrypted API key")
    api_secret: Mapped[str] = mapped_column(Text, nullable=False, comment="Encrypted API secret")
    store_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sync_config: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON sync configuration")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    products = relationship("Product", back_populates="store")
    orders = relationship("Order", back_populates="store")
    customers = relationship("Customer", back_populates="store")
