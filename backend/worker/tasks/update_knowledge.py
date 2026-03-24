import logging

from celery import chord, group

from worker.celery_app import app
from worker.services.site_parser import parse_site_with_metadata
from worker.services.merge_data import (
    merge_batches,
    split_batches,
    get_enabled_sources,
    save_chuck,
    save_new_faq,
)
from app.core.config import get_config
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

BATCH_SIZE = 5


@app.task(
    bind=True,
    name="worker.tasks.parsing.parse_single_site",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def parse_single_site(self, source: dict) -> list[dict]:
    results = parse_site_with_metadata(source)

    return results


@app.task(
    bind=True,
    name="worker.tasks.parsing.save_chunks_and_extract",
    max_retries=1,
)
def save_chunks_and_extract(self, nested_results: list[list[dict]]):
    results = merge_batches(nested_results)
    if not results:
        logger.warning("Ничего не спарсено")
        return

    save_chuck(results)

    config = get_config()
    if not config.polza_ai_api_key:
        logger.warning("POLZA_AI_API_KEY не задан")
        return

    batches = split_batches(results, BATCH_SIZE)
    logger.info("FAQ: %d батчей", len(batches))

    chord(
        group(process_batch.s(batch) for batch in batches),
        save_faq.s(),
    ).apply_async()


@app.task(
    bind=True,
    name="worker.tasks.parsing.process_batch",
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def process_batch(self, texts: list[dict]) -> list[dict]:
    if not texts:
        return []

    config = get_config()
    if not config.polza_ai_api_key:
        return []

    faq_items = AIService(config).extract_faq_from_texts(texts)
    return faq_items


@app.task(
    bind=True,
    name="worker.tasks.parsing.save_faq",
    max_retries=1,
)
def save_faq(self, faq_batches: list[list[dict]]):
    all_new = merge_batches(faq_batches)
    count = save_new_faq(all_new)
    if not count:
        logger.info("Новых уникальных FAQ нет")


@app.task(
    bind=True,
    name="worker.tasks.parsing.update_knowledge_base",
    max_retries=1,
)
def update_knowledge_base(self):
    enabled = get_enabled_sources()

    if not enabled:
        logger.warning("Нет активных источников")
        return

    chord(
        group(parse_single_site.s(s) for s in enabled),
        save_chunks_and_extract.s(),
    ).apply_async()
