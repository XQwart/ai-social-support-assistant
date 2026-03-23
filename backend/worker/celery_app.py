from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

from app.core.config import get_config
from app.core.logger import setup_logging

config = get_config()


@worker_process_init.connect
def init_worker(**kwargs):
    setup_logging(level=config.log_level)


app = Celery(
    "worker",
    broker=config.redis_celery_url,
    backend=config.redis_celery_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    # Не теряем задачи при перезапуске
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Celery Beat: запуск обновления базы знаний каждые 3 дня
app.conf.beat_schedule = {
    "update-knowledge-base-every-3-days": {
        "task": "worker.tasks.parsing.update_knowledge_base",
        "schedule": crontab(hour=3, minute=0, day_of_month="*/3"),
        "options": {"queue": "default"},
    },
}

# Автоматически находим задачи
app.autodiscover_tasks(["worker.tasks"])
