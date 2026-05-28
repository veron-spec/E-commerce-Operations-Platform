from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "E-Commerce Operations Platform"

    # Edition: "enterprise" (full features) or "community" (open-source)
    edition: str = "community"
    debug: bool = False
    secret_key: str = "change-me"
    encryption_key: str = "change-me"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_ops"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    sync_interval_minutes: int = 30
    report_cache_ttl_hours: int = 6

    # Security
    cors_origins: str = "http://localhost:8000,http://localhost:3000"
    rate_limit_enabled: bool = True
    max_request_size_mb: int = 5

    # Taobao OAuth
    taobao_redirect_uri: str = "http://localhost:17452/api/v1/auth/taobao/callback"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
