from celery import Celery

from app.core.config import get_config

config = get_config()


app = Celery("worker", broker=config.redis_celery_url, backend=config.redis_celery_url)
