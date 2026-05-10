"""Background worker entrypoints.

Celery app configuration for MixCut background job processing.
"""

from __future__ import annotations

from backend.config import get_settings


def create_celery_app():
    """Create and configure the Celery application."""
    from celery import Celery

    settings = get_settings()
    app = Celery(
        "mixcut",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
        task_soft_time_limit=600,
        task_time_limit=900,
        task_default_queue="mixcut_default",
        task_queues={
            "mixcut_default": {"exchange": "mixcut_default", "routing_key": "default"},
            "mixcut_jobs": {"exchange": "mixcut_jobs", "routing_key": "jobs"},
        },
    )
    app.autodiscover_tasks(["backend.workers"])
    return app


try:
    celery_app = create_celery_app()
except ImportError:
    celery_app = None
