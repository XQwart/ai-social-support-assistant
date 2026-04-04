from __future__ import annotations

from datetime import datetime, timezone

from worker.models.source import Source
from worker.repositories.source_repository import SourceRepository


class SourceService:
    def __init__(self, source_repository: SourceRepository) -> None:
        self._source_repository = source_repository

    def get_by_url(self, url: str) -> Source | None:
        return self._source_repository.get_by_url(url)

    def get_or_create_source(
        self,
        url: str,
        name: str | None = None,
    ) -> Source:
        source = self._source_repository.get_by_url(url)
        if source is not None:
            return source

        return self._source_repository.create_source(
            url=url,
            name=name,
        )

    def register_source_for_region(
        self,
        url: str,
        region_id: int,
        name: str | None = None,
    ) -> Source:
        source = self.get_or_create_source(
            url=url,
            name=name,
        )

        self._source_repository.add_region_to_source(
            source_id=source.id,
            region_id=region_id,
        )
        return source

    def claim_due_sources(self, limit: int) -> list[Source]:
        now = datetime.now(timezone.utc)
        return self._source_repository.claim_due_sources(
            now=now,
            limit=limit,
        )

    def release_stale_locks(self, threshold: datetime) -> int:
        return self._source_repository.release_stale_locks(
            threshold=threshold,
        )

    def mark_success(self, source_id: int) -> None:
        self._source_repository.mark_success(source_id=source_id)

    def mark_failed(self, source_id: int, error: str) -> None:
        self._source_repository.mark_failed(
            source_id=source_id,
            error=error,
        )

    def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        return self._source_repository.get_region_codes_by_source_id(
            source_id=source_id,
        )

    def build_qdrant_payload(self, source: Source) -> dict[str, object]:
        region_codes = self.get_region_codes_by_source_id(source.id)

        return {
            "source_id": source.id,
            "source_url": source.url,
            "source_name": source.name,
            "region_codes": region_codes,
        }
