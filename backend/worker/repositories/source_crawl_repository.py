from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from sqlalchemy import select, update, or_
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from worker.core.constants import DEFAULT_CRAWL_INTERVAL
from worker.models.source import Source
from shared.models.regions import Region, SourceRegion


class SourceCrawlRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def claim_due_sources(self, now: datetime, limit: int) -> list[Source]:
        stmt = (
            select(Source)
            .where(
                Source.is_locked.is_(False),
                Source.next_crawl_at.is_not(None),
                Source.next_crawl_at <= now,
                or_(
                    Source.last_error.is_(None),
                    Source.last_error != "empty",
                ),
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

    def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        stmt = (
            select(Region.code)
            .join(SourceRegion, SourceRegion.region_id == Region.id)
            .where(SourceRegion.source_id == source_id)
            .order_by(Region.code.asc())
        )
        return list(self._session.scalars(stmt).all())
