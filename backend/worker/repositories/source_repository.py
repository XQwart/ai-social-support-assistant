from __future__ import annotations

from datetime import datetime, timezone
from typing import cast
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.engine import CursorResult

from worker.models.source import Source
from worker.models.regions import Region, SourceRegion
from worker.core.constants import DEFAULT_CRAWL_INTERVAL


class SourceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_source(
        self,
        url: str,
        name: str | None = None,
    ) -> Source:
        source = Source(
            url=url,
            name=name,
            next_crawl_at=datetime.now(timezone.utc),
            crawl_interval_minutes=int(DEFAULT_CRAWL_INTERVAL.total_seconds() // 60),
        )
        self._session.add(source)
        self._session.flush()
        return source

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

    def claim_due_sources(self, now: datetime, limit: int) -> list[Source]:
        stmt = (
            select(Source)
            .where(
                Source.is_active.is_(True),
                Source.is_locked.is_(False),
                Source.next_crawl_at.is_not(None),
                Source.next_crawl_at <= now,
            )
            .order_by(Source.next_crawl_at.asc(), Source.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        sources = list(self._session.scalars(stmt).all())

        for source in sources:
            source.is_locked = True
            source.locked_at = now

        self._session.flush()
        return sources

    def release_stale_locks(self, threshold: datetime) -> int:
        stmt = (
            update(Source)
            .where(
                Source.is_locked.is_(True),
                Source.locked_at.is_not(None),
                Source.locked_at < threshold,
            )
            .values(
                is_locked=False,
                locked_at=None,
            )
        )

        result = cast(CursorResult, self._session.execute(stmt))
        self._session.flush()
        return result.rowcount

    def mark_success(self, source_id: int) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Source)
            .where(Source.id == source_id)
            .values(
                is_locked=False,
                locked_at=None,
                last_error=None,
                last_crawled_at=now,
                next_crawl_at=now + DEFAULT_CRAWL_INTERVAL,
            )
        )
        self._session.execute(stmt)
        self._session.flush()

    def mark_failed(self, source_id: int, error: str) -> None:
        stmt = (
            update(Source)
            .where(Source.id == source_id)
            .values(
                is_locked=False,
                locked_at=None,
                last_error=error[:1000],
            )
        )
        self._session.execute(stmt)
        self._session.flush()

    def get_by_url(self, url: str) -> Source | None:
        stmt = select(Source).where(Source.url == url)

        return self._session.scalar(stmt)

    def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        stmt = (
            select(Region.code)
            .join(SourceRegion, SourceRegion.region_id == Region.id)
            .where(SourceRegion.source_id == source_id)
            .order_by(Region.code.asc())
        )
        return list(self._session.scalars(stmt).all())
