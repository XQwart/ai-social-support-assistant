import logging
from datetime import datetime, timezone

from worker.utils.json_storage import load_json, save_json
from app.core.constants import FAQ_JSON, CHUCK_JSON, SOURCES_JSON

logger = logging.getLogger(__name__)


def merge_batches(nested: list[list[dict]]) -> list[dict]:
    results = []
    for batch in nested:
        if batch:
            results.extend(batch)

    return results


def split_batches(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def get_enabled_sources() -> list[dict]:
    sources = load_json(SOURCES_JSON, default=[])

    return [s for s in sources if s.get("enabled", True)]


def save_chuck(results: list[dict]) -> None:
    scraped_at = datetime.now(timezone.utc).isoformat()
    chuck_data = [
        {
            "source_id": item.get("source_id", ""),
            "source_url": item.get("source_url", ""),
            "source_name": item.get("source_name", ""),
            "page_label": item.get("page_label", ""),
            "region": item.get("region", ""),
            "region_code": item.get("region_code", ""),
            "category": item.get("category", "общие"),
            "text": item.get("text", "")[:10000],
            "last_scraped": scraped_at,
        }
        for item in results
    ]
    save_json(CHUCK_JSON, chuck_data)


def save_new_faq(new_faq: list[dict]) -> int:
    if not new_faq:
        return 0

    existing = load_json(FAQ_JSON, default=[])

    curr_faq = {item.get("question", "").strip().lower() for item in existing}

    unique = []
    for item in new_faq:
        q = item.get("question", "").strip().lower()
        if q and q not in curr_faq:
            unique.append(item)
            curr_faq.add(q)

    if not unique:
        return 0

    merged = existing + unique
    save_json(FAQ_JSON, merged)
    logger.info("faq.json: %d (+%d новых)", len(merged), len(unique))

    return len(unique)
