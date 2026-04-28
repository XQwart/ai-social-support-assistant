from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from worker.core.constants import DEFAULT_CRAWL_INTERVAL
from shared.models.regions import Region, SourceRegion
from worker.models.source import Source


class SourceRegistrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_source(
        self,
        url: str,
        document_type: str,
        place_of_work: str | None,
        name: str | None = None,
    ) -> tuple[Source, bool]:

        stmt = (
            pg_insert(Source)
            .values(
                url=url,
                name=name,
                next_crawl_at=datetime.now(timezone.utc),
                crawl_interval_minutes=int(
                    DEFAULT_CRAWL_INTERVAL.total_seconds() // 60
                ),
                document_type=document_type,
                place_of_work=place_of_work,
            )
            .on_conflict_do_nothing(
                index_elements=[Source.url],
            )
            .returning(Source.id)
        )

        result = await self._session.execute(stmt)
        created_source_id = result.scalar_one_or_none()

        if created_source_id is not None:
            source = await self._session.get(Source, created_source_id)

            if source is None:
                raise RuntimeError(
                    f"Source was created but not found by id={created_source_id}"
                )

            return source, True

        existing_source = await self.get_by_url(url)

        if existing_source is None:
            raise RuntimeError(f"Source was not created and not found by url={url}")

        return existing_source, False

    async def get_by_url(self, url: str) -> Source | None:
        stmt = select(Source).where(Source.url == url)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_region_to_source(self, source_id: int, region_id: int) -> None:
        stmt = (
            pg_insert(SourceRegion)
            .values(
                source_id=source_id,
                region_id=region_id,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    SourceRegion.source_id,
                    SourceRegion.region_id,
                ],
            )
        )

        await self._session.execute(stmt)

    async def get_existing_urls(self, urls: list[str]) -> set[str]:
        if not urls:
            return set()

        stmt = select(Source.url).where(Source.url.in_(urls))
        result = await self._session.execute(stmt)
        return set(result.scalars().all())

    async def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        stmt = (
            select(Region.code)
            .join(SourceRegion, SourceRegion.region_id == Region.id)
            .where(SourceRegion.source_id == source_id)
            .order_by(Region.code.asc())
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
