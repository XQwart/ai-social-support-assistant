from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, delete, or_, select, update, func

from shared.models import DocumentChunk, Region, SourceRegion
from worker.models.source import Source

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AdminChunkRepository:
    """Write-side repository for RAG chunks, used by the admin panel.

    Keeps the Qdrant-facing payload metadata in sync with Postgres so
    the only mutation path for indexed content is the admin-service
    service layer.
    """

    _session: "AsyncSession"

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Source helpers
    # ------------------------------------------------------------------
    async def list_sources(self) -> list[Source]:
        result = await self._session.execute(
            select(Source).order_by(Source.id.asc())
        )
        return list(result.scalars().all())

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

    # ------------------------------------------------------------------
    # Chunk listing / retrieval
    # ------------------------------------------------------------------
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
            needle = f"%{search.lower()}%"
            filters.append(
                or_(
                    func.lower(DocumentChunk.text).like(needle),
                    func.lower(DocumentChunk.source_name).like(needle),
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

    async def next_chunk_index(self, source_id: int) -> int:
        result = await self._session.execute(
            select(func.max(DocumentChunk.chunk_index)).where(
                DocumentChunk.source_id == source_id
            )
        )
        current = result.scalar_one_or_none()
        return int(current) + 1 if current is not None else 0

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    async def create(
        self,
        source_id: int,
        source_url: str,
        source_name: str | None,
        chunk_index: int,
        text: str,
        qdrant_point_id: UUID,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            source_id=source_id,
            source_url=source_url,
            source_name=source_name,
            chunk_index=chunk_index,
            text=text,
            qdrant_point_id=qdrant_point_id,
        )
        self._session.add(chunk)
        await self._session.flush()
        await self._session.refresh(chunk)
        return chunk

    async def update_text_and_point_id(
        self,
        chunk_id: int,
        text: str,
        qdrant_point_id: UUID,
    ) -> None:
        await self._session.execute(
            update(DocumentChunk)
            .where(DocumentChunk.id == chunk_id)
            .values(text=text, qdrant_point_id=qdrant_point_id)
        )

    async def delete(self, chunk_id: int) -> None:
        await self._session.execute(
            delete(DocumentChunk).where(DocumentChunk.id == chunk_id)
        )
