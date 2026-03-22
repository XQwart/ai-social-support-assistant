from celery import chord

from worker.celery_app import app
from worker.parsers.site_parser import parse_site


@app.task(
    bind=True,
    name="worker.tasks.parsing.parse_single_site",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def parse_single_site(self, site_url: str):
    text = parse_site(site_url)
