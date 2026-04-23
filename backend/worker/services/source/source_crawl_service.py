from __future__ import annotations

from datetime import datetime, timezone

from worker.models.source import Source
from worker.repositories.source_crawl_repository import SourceCrawlRepository


class SourceCrawlService:
    def __init__(self, source_repository: SourceCrawlRepository) -> None:
        self._source_repository = source_repository

    async def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        return await self._source_repository.get_region_codes_by_source_id(source_id)

    async def claim_due_sources(self, limit: int) -> list[Source]:
        now = datetime.now(timezone.utc)
        return await self._source_repository.claim_due_sources(
            now=now,
            limit=limit,
        )

    async def release_stale_locks(self, threshold: datetime) -> int:
        return await self._source_repository.release_stale_locks(
            threshold=threshold,
        )

    async def mark_success(self, source_id: int) -> None:
        await self._source_repository.mark_success(source_id=source_id)

    async def mark_failed(self, source_id: int, error: str) -> None:
        await self._source_repository.mark_failed(
            source_id=source_id,
            error=error,
        )
