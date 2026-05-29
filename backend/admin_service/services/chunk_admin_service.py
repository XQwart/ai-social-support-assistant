from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from admin_service.services.chunk_api_client import ChunkApiClient, ChunkApiError

if TYPE_CHECKING:
    from shared.models import DocumentChunk
    from worker.models.source import Source

    from admin_service.repositories.admin_chunk_repository import (
        AdminChunkRepository,
    )
    from admin_service.services.admin_audit_service import AdminAuditService


logger = logging.getLogger(__name__)


class ChunkValidationError(Exception):
    pass


class ChunkPersistenceError(Exception):
    pass


class ChunkAdminService:
    _repo: "AdminChunkRepository"
    _api: ChunkApiClient
    _audit: "AdminAuditService"

    def __init__(
        self,
        repo: "AdminChunkRepository",
        api: ChunkApiClient,
        audit: "AdminAuditService",
    ) -> None:
        self._repo = repo
        self._api = api
        self._audit = audit

    async def list_paginated(
        self,
        source_id: int | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list["DocumentChunk"], int]:
        return await self._repo.list_paginated(
            source_id=source_id, search=search, limit=limit, offset=offset
        )

    async def list_sources(self) -> list["Source"]:
        return await self._repo.list_sources()

    async def list_sources_paginated(
        self,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list["Source"], int]:
        return await self._repo.list_sources_paginated(
            search=search, limit=limit, offset=offset
        )

    async def list_regions(self):
        return await self._repo.list_regions()

    async def list_places_of_work(self) -> list[str]:
        return await self._repo.list_places_of_work()

    async def get_source_region_codes(self, source_id: int) -> list[str]:
        return await self._repo.get_source_region_codes(source_id)

    async def get_source(self, source_id: int):
        return await self._repo.get_source(source_id)

    async def get(self, chunk_id: int) -> "DocumentChunk | None":
        return await self._repo.get_by_id(chunk_id)

    async def create(
        self,
        source_id: int | None,
        text: str,
        admin_id: int,
        region_code: str | None = None,
        place_of_work: str | None = None,
        place_of_work_set: bool = False,
        source_url: str | None = None,
    ) -> dict:
        text = self._normalize(text)

        source = await self._repo.get_source(source_id) if source_id else None
        if source_id is not None and source is None:
            raise ChunkValidationError(f"Источник #{source_id} не найден.")

        effective_url = self._resolve_source_url(
            override=source_url, fallback=source.url if source else None
        )
        if not effective_url:
            raise ChunkValidationError(
                "Укажите ссылку на источник или выберите существующий документ."
            )

        effective_place = self._resolve_place_of_work(
            override=place_of_work,
            override_set=place_of_work_set,
            fallback=source.place_of_work if source else None,
        )
        effective_code, effective_region_name = await self._resolve_region(
            override=region_code,
            fallback_source_id=source.id if source else None,
        )

        try:
            result = await self._api.add_text(
                source_url=effective_url,
                source_name=source.name if source else None,
                region_code=effective_code,
                region_name=effective_region_name,
                place_of_work=effective_place,
                text=text,
            )
        except ChunkApiError as exc:
            raise ChunkPersistenceError(str(exc)) from exc

        await self._audit.record(
            action="chunk.created",
            admin_id=admin_id,
            target_type="source",
            target_id=str(result.get("source_id") or ""),
            payload_diff={
                "source_url": effective_url,
                "region_code": effective_code,
                "place_of_work": effective_place,
                "text_length": len(text),
                "chunks_count": result.get("chunks_count"),
                "status": result.get("status"),
            },
        )
        return result

    async def update(
        self,
        chunk_id: int,
        text: str,
        admin_id: int,
        place_of_work: str | None = None,
        place_of_work_set: bool = False,
    ) -> "DocumentChunk":
        text = self._normalize(text)

        chunk = await self._repo.get_by_id(chunk_id)
        if chunk is None:
            raise KeyError(chunk_id)

        effective_place = self._resolve_place_of_work(
            override=place_of_work,
            override_set=place_of_work_set,
            fallback=chunk.place_of_work,
        )

        previous_length = len(chunk.text)
        try:
            result = await self._api.update_chunk(
                chunk_id=chunk.id,
                text=text,
                place_of_work=effective_place,
            )
        except ChunkApiError as exc:
            raise ChunkPersistenceError(str(exc)) from exc

        await self._audit.record(
            action="chunk.updated",
            admin_id=admin_id,
            target_type="chunk",
            target_id=str(chunk.id),
            payload_diff={
                "previous_length": previous_length,
                "new_length": len(text),
                "place_of_work": effective_place,
                "status": result.get("status"),
            },
        )

        refreshed = await self._repo.get_by_id(chunk.id)
        assert refreshed is not None
        return refreshed

    async def delete(self, chunk_id: int, admin_id: int) -> None:
        chunk = await self._repo.get_by_id(chunk_id)
        if chunk is None:
            return

        try:
            result = await self._api.delete_chunk(chunk.id)
        except ChunkApiError as exc:
            raise ChunkPersistenceError(str(exc)) from exc

        await self._audit.record(
            action="chunk.deleted",
            admin_id=admin_id,
            target_type="chunk",
            target_id=str(chunk.id),
            payload_diff={
                "qdrant_point_id": str(chunk.qdrant_point_id),
                "status": result.get("status"),
            },
        )

    async def _resolve_region(
        self,
        override: str | None,
        fallback_source_id: int | None,
    ) -> tuple[str | None, str | None]:
        cleaned = (override or "").strip()
        if cleaned:
            name = await self._region_name_for_code(cleaned)
            return (cleaned, name) if name else (None, None)

        if fallback_source_id is None:
            return None, None

        source_codes = await self._repo.get_source_region_codes(fallback_source_id)
        if not source_codes:
            return None, None

        first = source_codes[0]
        name = await self._region_name_for_code(first)
        return (first, name) if name else (None, None)

    async def _region_name_for_code(self, code: str) -> str | None:
        regions = await self._repo.list_regions()
        for region in regions:
            if region.code == code:
                return region.name
        return None

    @staticmethod
    def _resolve_place_of_work(
        override: str | None, override_set: bool, fallback: str | None
    ) -> str | None:
        if not override_set:
            return fallback
        cleaned = (override or "").strip()
        return cleaned or None

    @staticmethod
    def _resolve_source_url(
        override: str | None, fallback: str | None
    ) -> str | None:
        cleaned = (override or "").strip()
        return cleaned or fallback

    @staticmethod
    def _normalize(text: str) -> str:
        text = (text or "").strip()
        if not text:
            raise ChunkValidationError("Текст чанка не может быть пустым.")
        if len(text) < 50:
            raise ChunkValidationError(
                "Слишком короткий чанк: минимум 50 символов."
            )
        if len(text) > 16_000:
            raise ChunkValidationError(
                "Слишком длинный чанк: ограничение 16000 символов."
            )
        return text
