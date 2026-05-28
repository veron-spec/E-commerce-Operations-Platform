from celery import Celery

from app.config import settings

celery_app = Celery(
    "ecommerce_ops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# 鈹€鈹€ Pro tasks beat schedule (only when pro/ package is available) 鈹€鈹€
_beat_schedule = {}

try:
    import app.pro  # noqa: F401
    _beat_schedule.update({
        "sync-all-stores": {
            "task": "tasks.sync_tasks.sync_all_stores",
            "schedule": settings.sync_interval_minutes * 60,
        },
        "scan-product-selections": {
            "task": "tasks.product_selection_tasks.scan_product_selections",
            "schedule": 86400,  # daily
        },
    })
except ImportError:
    pass

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    beat_schedule=_beat_schedule,    imports=(
        "tasks.sync_tasks",
        "tasks.product_selection_tasks",
        "tasks.report_tasks",
    ),
)
