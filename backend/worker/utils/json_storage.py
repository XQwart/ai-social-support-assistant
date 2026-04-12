from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from worker.core.config import get_config
from worker.db.session import create_session
from worker.models.regions import Region, SourceRegion
from worker.models.source import Source
from worker.repositories.source_repository import SourceRepository
from worker.services.source_service import SourceService

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


def get_or_create_region(
    session: Session,
    code: str,
    name: str,
) -> Region:
    stmt = select(Region).where(Region.code == code)
    region = session.scalar(stmt)

    if region is not None:
        if region.name != name:
            region.name = name
            session.flush()
        return region

    region = Region(
        code=code,
        name=name,
    )
    session.add(region)
    session.flush()
    return region


def clear_all(session: Session) -> None:
    deleted_links = session.query(SourceRegion).delete()
    deleted_sources = session.query(Source).delete()
    deleted_regions = session.query(Region).delete()

    logger.warning(
        "Удалено связей: %d, source: %d, regions: %d",
        deleted_links,
        deleted_sources,
        deleted_regions,
    )
    session.flush()


def seed(session: Session, regions_data: list[dict], clear: bool = False) -> None:
    source_repository = SourceRepository(session)
    source_service = SourceService(source_repository)

    if clear:
        clear_all(session)

    added_sources = 0
    existing_sources = 0
    added_links = 0

    for item in regions_data:
        region_name = item["region"]
        region_code = str(item["code"]).zfill(2)
        urls = item.get("url", [])

        region = get_or_create_region(
            session=session,
            code=region_code,
            name=region_name,
        )

        for url in urls:
            existing_source = source_service.get_by_url(url)

            before_codes: set[str] = set()
            if existing_source is not None:
                existing_sources += 1
                before_codes = set(
                    source_service.get_region_codes_by_source_id(existing_source.id)
                )

            source = source_service.register_source_for_region(
                url=url,
                region_id=region.id,
                name=region_name,
            )

            if existing_source is None:
                added_sources += 1

            after_codes = set(source_service.get_region_codes_by_source_id(source.id))

            if after_codes != before_codes:
                added_links += 1

        logger.debug(
            "Регион %s (код %s): %d URL",
            region_name,
            region_code,
            len(urls),
        )

    session.commit()
    logger.info(
        "Добавлено source: %d, найдено существующих source: %d, добавлено связей source-region: %d",
        added_sources,
        existing_sources,
        added_links,
    )


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
        help="Удалить все source, region и связи перед загрузкой",
    )
    args = parser.parse_args()

    config = get_config()
    session_factory = create_session(config.database_url)
    session = session_factory()

    try:
        regions_data = load_json(args.file)
        seed(session, regions_data, clear=args.clear)
    except Exception:
        session.rollback()
        logger.exception("Ошибка загрузки sources")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
