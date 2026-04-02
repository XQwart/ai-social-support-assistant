from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from worker.core.config import get_config
from worker.models.source import Source
from worker.db.session import create_session

logger = logging.getLogger(__name__)

DEFAULT_FILE = Path(__file__).parent.parent / "data" / "full_regions.json"


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        logger.error("Файл не найден: %s", path)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    logger.info("Загружено %d регионов из %s", len(data), path)
    return data


def seed(session: Session, regions: list[dict], clear: bool = False) -> None:
    if clear:
        deleted = session.query(Source).delete()
        logger.warning("Удалено %d старых source", deleted)

    now = datetime.now(timezone.utc)
    added = 0
    skipped = 0

    for region in regions:
        region_name = region["region"]
        region_code = int(region["code"])
        urls = region.get("url", [])

        for url in urls:
            exists = session.query(Source.id).filter_by(url=url).first()

            if exists:
                logger.debug("Уже существует: %s", url)
                skipped += 1
                continue

            source = Source(
                name=region_name,
                url=url,
                region=region_name,
                region_code=region_code,
                is_active=True,
                next_crawl_at=now,
            )
            session.add(source)
            added += 1

        logger.debug(
            "Регион %s (код %d): %d URL",
            region_name,
            region_code,
            len(urls),
        )

    session.commit()
    logger.info("Добавлено: %d, пропущено (дубли): %d", added, skipped)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(description="Загрузка sources в БД")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FILE,
        help="Путь к JSON-файлу",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Удалить все source перед загрузкой",
    )
    args = parser.parse_args()

    config = get_config()
    session_factory = create_session(config.database_url)
    session = session_factory()

    try:
        regions = load_json(args.file)
        seed(session, regions, clear=args.clear)
    except Exception:
        session.rollback()
        logger.exception("Ошибка загрузки sources")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
