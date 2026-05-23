from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=1)
    suggestion_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="restock / price_adjustment / marketing_campaign / inventory_optimization")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", comment="high / medium / low")
    data_source: Mapped[str] = mapped_column(String(100), nullable=False, comment="inventory_analyzer / sales_analyzer / trend_analyzer")
    related_metrics: Mapped[dict[Any, Any] | None] = mapped_column(JSON, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="pending", comment="pending / applied / dismissed")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
