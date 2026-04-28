import logging
from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging, worker_shutdown
from worker.core.config import get_config


@setup_logging.connect
def on_setup_logging(**kwargs):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,
    )


config = get_config()


app = Celery(
    "worker",
    broker=config.redis_celery_url,
    backend=config.redis_celery_url,
    include=[
        "worker.tasks.update_knowledge_task",
        "worker.tasks.scheduler_task",
        "worker.tasks.get_source_link_task",
        "worker.tasks.import_one_source_task",
        "worker.tasks.finalize_source_import_task",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

app.conf.beat_schedule = {
    "dispatch-due-crawls-every-15-minutes": {
        "task": "worker.tasks.scheduler_task.dispatch_due_crawls",
        "schedule": crontab(minute="*/15"),
    },
    "get-source-links-every-2-months": {
        "task": "worker.tasks.get_source_link_task.get_source_links",
        "schedule": crontab(minute=0, hour=4, month_of_year="*/2", day_of_month=1),
    },
    "reap-stale-locks-every-50-minutes": {
        "task": "worker.tasks.scheduler_task.reap_stale_locks",
        "schedule": crontab(minute="*/50"),
    },
}


@worker_shutdown.connect
def cleanup_on_shutdown(**kwargs):
    from worker.dependencies.runtime import AsyncRuntime

    runtime = AsyncRuntime.get()
    runtime.close()
