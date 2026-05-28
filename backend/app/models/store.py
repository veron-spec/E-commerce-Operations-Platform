from datetime import datetime

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="shopify, woocommerce, etc.")
    api_key: Mapped[str] = mapped_column(Text, nullable=False, comment="Encrypted API key")
    api_secret: Mapped[str] = mapped_column(Text, nullable=False, comment="Encrypted API secret")
    store_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sync_config: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON sync configuration")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Taobao OAuth tokens (encrypted via crypto.py)
    session_key: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Encrypted Taobao session_key (access_token)")
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Encrypted Taobao refresh_token")
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="Taobao access_token expiry")

    # relationships
    owner = relationship("User", backref="stores")
    products = relationship("Product", back_populates="store")
    orders = relationship("Order", back_populates="store")
    customers = relationship("Customer", back_populates="store")
