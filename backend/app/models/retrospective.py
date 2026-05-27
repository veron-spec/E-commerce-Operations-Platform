from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class Retrospective(Base):
    __tablename__ = "retrospectives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=1)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="weekly / monthly / quarterly")
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_summary: Mapped[dict[Any, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metrics_snapshot: Mapped[dict[Any, Any]] = mapped_column(JSON, nullable=False, default=dict)
    comparisons: Mapped[dict[Any, Any] | None] = mapped_column(JSON, nullable=True, default=dict)
    insights: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    action_items: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    status: Mapped[str] = mapped_column(String(50), default="draft", comment="draft / published / archived")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
