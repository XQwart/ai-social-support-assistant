from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from worker.core.constants import DEFAULT_CRAWL_INTERVAL
from worker.models.regions import Region, SourceRegion
from worker.models.source import Source


class SourceRegistrationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_source(
        self,
        url: str,
        document_type: str,
        place_of_work: str | None,
        name: str | None = None,
    ) -> Source:
        source = Source(
            url=url,
            name=name,
            next_crawl_at=datetime.now(timezone.utc),
            crawl_interval_minutes=int(DEFAULT_CRAWL_INTERVAL.total_seconds() // 60),
            document_type=document_type,
            place_of_work=place_of_work,
        )
        self._session.add(source)
        self._session.flush()
        return source

    def get_by_url(self, url: str) -> Source | None:
        stmt = select(Source).where(Source.url == url)
        return self._session.scalar(stmt)

    def add_region_to_source(self, source_id: int, region_id: int) -> None:
        stmt = select(SourceRegion).where(
            SourceRegion.source_id == source_id,
            SourceRegion.region_id == region_id,
        )
        existing = self._session.scalar(stmt)
        if existing is not None:
            return

        self._session.add(
            SourceRegion(
                source_id=source_id,
                region_id=region_id,
            )
        )
        self._session.flush()

    def get_existing_urls(self, urls: list[str]) -> set[str]:
        if not urls:
            return set()

        stmt = select(Source.url).where(Source.url.in_(urls))
        return set(self._session.scalars(stmt).all())

    def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        stmt = (
            select(Region.code)
            .join(SourceRegion, SourceRegion.region_id == Region.id)
            .where(SourceRegion.source_id == source_id)
            .order_by(Region.code.asc())
        )
        return list(self._session.scalars(stmt).all())
