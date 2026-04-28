from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from sqlalchemy import or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from worker.core.constants import DEFAULT_CRAWL_INTERVAL
from worker.models.source import Source
from shared.models.regions import Region, SourceRegion


class SourceCrawlRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim_due_sources(self, now: datetime, limit: int) -> list[Source]:
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

        result = await self._session.execute(stmt)
        sources = list(result.scalars().all())

        for source in sources:
            source.is_locked = True
            source.locked_at = now

        await self._session.flush()
        return sources

    async def release_stale_locks(self, threshold: datetime) -> int:
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

        result = cast(CursorResult, await self._session.execute(stmt))
        await self._session.flush()
        return result.rowcount or 0

    async def mark_success(self, source_id: int) -> None:
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

        await self._session.execute(stmt)
        await self._session.flush()

    async def mark_failed(self, source_id: int, error: str) -> None:
        stmt = (
            update(Source)
            .where(Source.id == source_id)
            .values(
                is_locked=False,
                locked_at=None,
                last_error=error[:1000],
            )
        )

        await self._session.execute(stmt)
        await self._session.flush()

    async def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        stmt = (
            select(Region.code)
            .join(SourceRegion, SourceRegion.region_id == Region.id)
            .where(SourceRegion.source_id == source_id)
            .order_by(Region.code.asc())
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
