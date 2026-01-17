"""Celery application for background tasks."""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "science_digest",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
