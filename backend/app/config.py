from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "E-Commerce Operations Platform"
    debug: bool = False
    secret_key: str = "change-me"
    encryption_key: str = "change-me"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_ops"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    sync_interval_minutes: int = 30
    report_cache_ttl_hours: int = 6

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
