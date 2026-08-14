import secrets
import os

from pydantic_settings import BaseSettings


def _default_key() -> str:
    """Generate a random 32-byte hex key as fallback when env var is not set."""
    return secrets.token_hex(32)


class Settings(BaseSettings):
    app_name: str = "E-Commerce Operations Platform"

    # Edition: "enterprise" (full features) or "community" (open-source)
    edition: str = "community"
    debug: bool = False
    secret_key: str = _default_key()
    encryption_key: str = _default_key()

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_ops"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    sync_interval_minutes: int = 30
    report_cache_ttl_hours: int = 6

    # Security
    cors_origins: str = "http://localhost:8000,http://localhost:3000"
    rate_limit_enabled: bool = True
    max_request_size_mb: int = 5

    # 部署子路径（空字符串=根路径，例如 "/cello"= https://domain/cello/）
    root_path: str = ""

    # Taobao OAuth
    taobao_redirect_uri: str = "http://localhost:17452/api/v1/auth/taobao/callback"

    # Vercel runtime configuration. These values remain optional for local development.
    app_base_url: str = ""
    init_schema_on_startup: bool = False
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""
    qstash_url: str = "https://qstash.upstash.io"
    qstash_token: str = ""
    qstash_current_signing_key: str = ""
    qstash_next_signing_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_vercel(self) -> bool:
        return os.getenv("VERCEL") == "1"

    @property
    def resolved_upstash_redis_rest_url(self) -> str:
        return self.upstash_redis_rest_url or os.getenv("UPSTASH_REDIS_REST_KV_REST_API_URL", "")

    @property
    def resolved_upstash_redis_rest_token(self) -> str:
        return self.upstash_redis_rest_token or os.getenv("UPSTASH_REDIS_REST_KV_REST_API_TOKEN", "")

    def validate_runtime(self) -> None:
        if not self.is_vercel:
            return

        required = (
            "DATABASE_URL",
            "SECRET_KEY",
            "ENCRYPTION_KEY",
            "QSTASH_TOKEN",
            "QSTASH_CURRENT_SIGNING_KEY",
            "QSTASH_NEXT_SIGNING_KEY",
            "APP_BASE_URL",
        )
        missing = [name for name in required if not os.getenv(name)]
        if not self.resolved_upstash_redis_rest_url:
            missing.append("UPSTASH_REDIS_REST_URL")
        if not self.resolved_upstash_redis_rest_token:
            missing.append("UPSTASH_REDIS_REST_TOKEN")
        if missing:
            raise RuntimeError("Missing required Vercel environment variables: " + ", ".join(missing))


settings = Settings()
