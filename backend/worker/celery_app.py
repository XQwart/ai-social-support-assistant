import logging

from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging as celery_setup_logging

from worker.core.config import get_config

config = get_config()


@celery_setup_logging.connect
def on_setup_logging(**kwargs):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,
    )


app = Celery(
    "worker",
    broker=config.redis_celery_url,
    backend=config.redis_celery_url,
    include=["worker.tasks.update_knowledge"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_hijack_root_logger=False,
)

app.conf.beat_schedule = {
    "update-knowledge-base-every-3-days": {
        "task": "worker.tasks.parsing.update_knowledge_base",
        "schedule": crontab(hour=3, minute=0, day_of_month="*/3"),
        "options": {"queue": "default"},
    },
}
