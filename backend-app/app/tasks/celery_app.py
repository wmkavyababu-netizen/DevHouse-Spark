from celery import Celery

from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "tarang_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.pipeline_tasks",
        "app.tasks.retraining_tasks",
    ],
)

# Standard Celery worker configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,       # 1 hour hard limit for long surveys
    task_soft_time_limit=3300,  # 55 minutes soft warning limit
    worker_prefetch_multiplier=1,
)
