from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import and_, or_, select, func

from shared.models import DocumentChunk, Region, SourceRegion
from worker.models.source import Source

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AdminChunkRepository:
    _session: "AsyncSession"

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session

    async def list_sources(self) -> list[Source]:
        result = await self._session.execute(
            select(Source).order_by(Source.id.asc())
        )
        return list(result.scalars().all())

    async def list_sources_paginated(
        self,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Source], int]:
        filters = []
        if search:
            needle = f"%{search}%"
            filters.append(
                or_(
                    Source.name.ilike(needle),
                    Source.url.ilike(needle),
                )
            )

        total_stmt = select(func.count(Source.id))
        if filters:
            total_stmt = total_stmt.where(and_(*filters))
        total = (await self._session.execute(total_stmt)).scalar_one()

        stmt = (
            select(Source)
            .order_by(Source.id.asc())
            .limit(limit)
            .offset(offset)
        )
        if filters:
            stmt = stmt.where(and_(*filters))
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), int(total)

    async def get_source(self, source_id: int) -> Source | None:
        result = await self._session.execute(
            select(Source).where(Source.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_source_region_codes(self, source_id: int) -> list[str]:
        result = await self._session.execute(
            select(Region.code)
            .join(SourceRegion, SourceRegion.region_id == Region.id)
            .where(SourceRegion.source_id == source_id)
        )
        return [row[0] for row in result.all()]

    async def list_regions(self) -> list[Region]:
        result = await self._session.execute(
            select(Region).order_by(Region.name.asc())
        )
        return list(result.scalars().all())

    async def list_places_of_work(self) -> list[str]:
        result = await self._session.execute(
            select(Source.place_of_work)
            .where(Source.place_of_work.is_not(None))
            .distinct()
        )
        return sorted({row[0] for row in result.all() if row[0]})

    async def list_paginated(
        self,
        source_id: int | None = None,
        search: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[DocumentChunk], int]:
        filters = []
        if source_id is not None:
            filters.append(DocumentChunk.source_id == source_id)
        if search:
            needle = f"%{search}%"
            filters.append(
                or_(
                    DocumentChunk.text.ilike(needle),
                    DocumentChunk.source_name.ilike(needle),
                    DocumentChunk.source_url.ilike(needle),
                )
            )

        total_stmt = select(func.count(DocumentChunk.id))
        if filters:
            total_stmt = total_stmt.where(and_(*filters))
        total = (await self._session.execute(total_stmt)).scalar_one()

        stmt = (
            select(DocumentChunk)
            .order_by(DocumentChunk.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if filters:
            stmt = stmt.where(and_(*filters))
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), int(total)

    async def get_by_id(self, chunk_id: int) -> DocumentChunk | None:
        result = await self._session.execute(
            select(DocumentChunk).where(DocumentChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()
