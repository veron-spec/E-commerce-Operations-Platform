from celery import Celery

from app.config import settings

celery_app = Celery(
    "ecommerce_ops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    beat_schedule={
        "sync-all-stores": {
            "task": "tasks.sync_tasks.sync_all_stores",
            "schedule": settings.sync_interval_minutes * 60,
        },
        "scan-product-selections": {
            "task": "tasks.product_selection_tasks.scan_product_selections",
            "schedule": 86400,  # daily
        },
        "generate-weekly-retrospective": {
            "task": "tasks.retrospective_tasks.generate_weekly_retrospective",
            "schedule": 604800,  # weekly
        },
    },
)
