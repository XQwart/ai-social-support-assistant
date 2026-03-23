import json
import logging
from datetime import datetime, timezone

from worker.celery_app import app
from worker.parsers.site_parser import parse_site_with_metadata
from app.core.constants import SOURCES_JSON, FAQ_JSON, CHUCK_JSON
from app.services.ai_service import AIService
from app.core.config import get_config

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    name="worker.tasks.parsing.parse_single_site",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def parse_single_site(self, source: dict) -> dict | None:
    """Спарсить один сайт из sources.json.

    Args:
        source: словарь с данными источника (id, url, region, ...)

    Returns:
        Словарь с текстом и метаданными, или None
    """
    logger.info("Парсим: %s (%s)", source.get("name", "?"), source.get("url", "?"))
    result = parse_site_with_metadata(source)

    if result:
        logger.info("Успешно спарсили %s (%d символов)", source.get("url"), len(result["text"]))
    else:
        logger.warning("Не удалось спарсить %s", source.get("url"))

    return result


@app.task(
    bind=True,
    name="worker.tasks.parsing.process_batch",
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_batch(self, texts: list[dict]) -> list[dict]:
    """Обработать батч из текстов через LLM для извлечения Q&A.

    Args:
        texts: список словарей с text, source_url, region и т.д.

    Returns:
        Список извлечённых Q&A пар
    """
    if not texts:
        return []

    config = get_config()
    if not config.polza_ai_api_key:
        logger.warning("POLZA_AI_API_KEY не задан — пропускаем извлечение FAQ")
        return []

    ai_service = AIService(config)
    faq_items = ai_service.extract_faq_from_texts(texts)

    logger.info("Извлечено %d FAQ-пар из батча из %d текстов", len(faq_items), len(texts))
    return faq_items


@app.task(
    bind=True,
    name="worker.tasks.parsing.update_knowledge_base",
    max_retries=1,
)
def update_knowledge_base(self):
    """Основная задача: обновить базу знаний.

    1. Загружаем sources.json
    2. Парсим все включённые источники
    3. Сохраняем в chuck.json
    4. Батчами по 5 отправляем в LLM
    5. Обновляем faq.json (с дедупликацией)
    """
    logger.info("=== Начинаем обновление базы знаний ===")

    # 1. Загружаем источники
    if not SOURCES_JSON.exists():
        logger.error("Файл sources.json не найден: %s", SOURCES_JSON)
        return

    try:
        sources = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Ошибка чтения sources.json: %s", e)
        return

    enabled_sources = [s for s in sources if s.get("enabled", True)]
    logger.info("Найдено %d активных источников из %d", len(enabled_sources), len(sources))

    # 2. Парсим все источники
    parsed_results: list[dict] = []
    for source in enabled_sources:
        try:
            result = parse_site_with_metadata(source)
            if result:
                parsed_results.append(result)
        except Exception as e:
            logger.error("Ошибка парсинга %s: %s", source.get("url"), e)
            continue

    logger.info("Успешно спарсено %d из %d источников", len(parsed_results), len(enabled_sources))

    if not parsed_results:
        logger.warning("Ничего не спарсено — завершаем")
        return

    # 3. Сохраняем в chuck.json (полные тексты для цитирования)
    chuck_data = []
    for item in parsed_results:
        chuck_data.append({
            "source_id": item["source_id"],
            "source_url": item["source_url"],
            "source_name": item["source_name"],
            "region": item["region"],
            "region_code": item["region_code"],
            "category": item["category"],
            "text": item["text"][:10000],  # Ограничиваем размер статьи
            "last_scraped": datetime.now(timezone.utc).isoformat(),
        })

    try:
        CHUCK_JSON.write_text(
            json.dumps(chuck_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Сохранено %d статей в chuck.json", len(chuck_data))
    except OSError as e:
        logger.error("Ошибка записи chuck.json: %s", e)

    # 4. Батчами по 5 отправляем в LLM для извлечения FAQ
    config = get_config()
    if not config.polza_ai_api_key:
        logger.warning("POLZA_AI_API_KEY не задан — пропускаем извлечение FAQ")
        return

    ai_service = AIService(config)

    # Загружаем существующие FAQ для дедупликации
    existing_faq: list[dict] = []
    try:
        if FAQ_JSON.exists():
            content = FAQ_JSON.read_text(encoding="utf-8")
            if content.strip():
                existing_faq = json.loads(content)
    except (json.JSONDecodeError, OSError):
        pass

    existing_questions = {
        item.get("question", "").strip().lower() for item in existing_faq
    }

    new_faq_items: list[dict] = []
    batch_size = 5

    for i in range(0, len(parsed_results), batch_size):
        batch = parsed_results[i : i + batch_size]
        logger.info("Обрабатываем батч %d/%d", i // batch_size + 1,
                     (len(parsed_results) + batch_size - 1) // batch_size)

        try:
            faq_items = ai_service.extract_faq_from_texts(batch)

            for item in faq_items:
                question = item.get("question", "").strip().lower()
                if question and question not in existing_questions:
                    new_faq_items.append(item)
                    existing_questions.add(question)

        except Exception as e:
            logger.error("Ошибка обработки батча: %s", e)
            continue

    logger.info("Извлечено %d новых FAQ-пар", len(new_faq_items))

    # 5. Обновляем faq.json
    if new_faq_items:
        all_faq = existing_faq + new_faq_items
        try:
            FAQ_JSON.write_text(
                json.dumps(all_faq, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Обновлён faq.json: всего %d записей (+%d новых)",
                        len(all_faq), len(new_faq_items))
        except OSError as e:
            logger.error("Ошибка записи faq.json: %s", e)

    logger.info("=== Обновление базы знаний завершено ===")
