from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class ThirdPartyKey(Base):
    """用户配置的第三方 API 密钥（如 OpenAI、Claude 等），
    用于自动化运营时调用外部 AI 服务，消耗用户自己的额度。"""

    __tablename__ = "third_party_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, comment="openai / claude / deepseek / etc.")
    label: Mapped[str] = mapped_column(String(100), nullable=False, comment="用户自定义名称，如「我的 OpenAI Key」")
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False, comment="AES 加密后的 API Key")
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, comment="明文前缀用于展示，如 sk-abc...")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
