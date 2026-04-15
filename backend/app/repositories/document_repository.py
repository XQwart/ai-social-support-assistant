from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select

from shared.models import DocumentChunk

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DocumentRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_ids(self, ids: list[int]) -> list[DocumentChunk]:
        result = await self._session.execute(
            select(DocumentChunk).where(DocumentChunk.id.in_(ids))
        )

        return list(result.scalars().all())
