from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from uuid import uuid4

from qdrant_client import models as qmodels

if TYPE_CHECKING:
    from langchain_core.embeddings.embeddings import Embeddings
    from qdrant_client import AsyncQdrantClient

    from shared.models import DocumentChunk
    from worker.models.source import Source

    from admin_service.repositories.admin_chunk_repository import (
        AdminChunkRepository,
    )
    from admin_service.services.admin_audit_service import AdminAuditService


logger = logging.getLogger(__name__)


class ChunkValidationError(Exception):
    """Raised on bad input from the chunk admin UI."""


class ChunkPersistenceError(Exception):
    """Raised when re-embedding or Qdrant upsert fails."""


class ChunkAdminService:
    """Write path for RAG chunks (with synchronous re-embedding).

    Every create/update produces a fresh embedding via the configured
    Embeddings client and upserts into Qdrant by stable UUID. The same
    UUID is persisted on the ``chunks`` row so subsequent edits can
    target the exact vector without scanning Qdrant payloads.
    """

    _repo: "AdminChunkRepository"
    _qdrant: "AsyncQdrantClient"
    _embedding: "Embeddings"
    _audit: "AdminAuditService"
    _collection: str

    def __init__(
        self,
        repo: "AdminChunkRepository",
        qdrant: "AsyncQdrantClient",
        embedding: "Embeddings",
        audit: "AdminAuditService",
        collection: str,
    ) -> None:
        self._repo = repo
        self._qdrant = qdrant
        self._embedding = embedding
        self._audit = audit
        self._collection = collection

    # ------------------------------------------------------------------
    # Read-side helpers (used by routes for listing/forms)
    # ------------------------------------------------------------------
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

    async def get(self, chunk_id: int) -> "DocumentChunk | None":
        return await self._repo.get_by_id(chunk_id)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    async def create(
        self,
        source_id: int,
        text: str,
        admin_id: int,
    ) -> "DocumentChunk":
        text = self._normalize(text)
        source = await self._require_source(source_id)
        region_codes = await self._repo.get_source_region_codes(source_id)
        place_of_work = source.place_of_work

        chunk_index = await self._repo.next_chunk_index(source_id)
        point_id = uuid4()
        vector = await self._embed(text)

        await self._upsert_qdrant(
            point_id=point_id,
            vector=vector,
            payload=self._build_payload(
                text_id=None,
                source_id=source.id,
                region_codes=region_codes,
                place_of_work=place_of_work,
                chunk_index=chunk_index,
                total_chunks=chunk_index + 1,
            ),
        )

        chunk = await self._repo.create(
            source_id=source.id,
            source_url=source.url,
            source_name=source.name,
            chunk_index=chunk_index,
            text=text,
            qdrant_point_id=point_id,
        )

        # text_id is the chunk PK; rewrite payload now that we have it.
        await self._upsert_qdrant(
            point_id=point_id,
            vector=vector,
            payload=self._build_payload(
                text_id=chunk.id,
                source_id=source.id,
                region_codes=region_codes,
                place_of_work=place_of_work,
                chunk_index=chunk_index,
                total_chunks=chunk_index + 1,
            ),
        )

        await self._audit.record(
            action="chunk.created",
            admin_id=admin_id,
            target_type="chunk",
            target_id=str(chunk.id),
            payload_diff={
                "source_id": source.id,
                "qdrant_point_id": str(point_id),
                "text_length": len(text),
            },
        )
        return chunk

    async def update(
        self,
        chunk_id: int,
        text: str,
        admin_id: int,
    ) -> "DocumentChunk":
        text = self._normalize(text)
        chunk = await self._repo.get_by_id(chunk_id)
        if chunk is None:
            raise KeyError(chunk_id)

        source = await self._require_source(chunk.source_id)
        region_codes = await self._repo.get_source_region_codes(source.id)
        place_of_work = source.place_of_work

        point_id = chunk.qdrant_point_id or uuid4()
        vector = await self._embed(text)

        await self._upsert_qdrant(
            point_id=point_id,
            vector=vector,
            payload=self._build_payload(
                text_id=chunk.id,
                source_id=source.id,
                region_codes=region_codes,
                place_of_work=place_of_work,
                chunk_index=chunk.chunk_index,
                total_chunks=chunk.chunk_index + 1,
            ),
        )

        previous_length = len(chunk.text)
        await self._repo.update_text_and_point_id(
            chunk_id=chunk.id,
            text=text,
            qdrant_point_id=point_id,
        )

        await self._audit.record(
            action="chunk.updated",
            admin_id=admin_id,
            target_type="chunk",
            target_id=str(chunk.id),
            payload_diff={
                "previous_length": previous_length,
                "new_length": len(text),
                "qdrant_point_id": str(point_id),
            },
        )

        refreshed = await self._repo.get_by_id(chunk.id)
        assert refreshed is not None
        return refreshed

    async def delete(self, chunk_id: int, admin_id: int) -> None:
        chunk = await self._repo.get_by_id(chunk_id)
        if chunk is None:
            return

        if chunk.qdrant_point_id is not None:
            try:
                await self._qdrant.delete(
                    collection_name=self._collection,
                    points_selector=qmodels.PointIdsList(
                        points=[str(chunk.qdrant_point_id)]
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "ChunkAdminService: Qdrant delete failed for chunk=%s",
                    chunk_id,
                )
                raise ChunkPersistenceError(
                    f"Не удалось удалить вектор в Qdrant: {exc}"
                ) from exc

        await self._repo.delete(chunk.id)

        await self._audit.record(
            action="chunk.deleted",
            admin_id=admin_id,
            target_type="chunk",
            target_id=str(chunk.id),
            payload_diff={"qdrant_point_id": str(chunk.qdrant_point_id)},
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _require_source(self, source_id: int) -> "Source":
        source = await self._repo.get_source(source_id)
        if source is None:
            raise ChunkValidationError(f"Источник #{source_id} не найден.")
        return source

    @staticmethod
    def _normalize(text: str) -> str:
        text = (text or "").strip()
        if not text:
            raise ChunkValidationError("Текст чанка не может быть пустым.")
        if len(text) > 16_000:
            raise ChunkValidationError(
                "Слишком длинный чанк: ограничение 16000 символов."
            )
        return text

    async def _embed(self, text: str) -> list[float]:
        try:
            vectors = await self._embedding.aembed_documents([text])
        except Exception as exc:  # noqa: BLE001
            logger.exception("ChunkAdminService: embedding failed")
            raise ChunkPersistenceError(
                f"Не удалось получить эмбеддинг: {exc}"
            ) from exc
        if not vectors or not vectors[0]:
            raise ChunkPersistenceError("Эмбеддинг вернул пустой вектор.")
        return vectors[0]

    async def _upsert_qdrant(
        self,
        point_id,
        vector: list[float],
        payload: dict,
    ) -> None:
        try:
            await self._qdrant.upsert(
                collection_name=self._collection,
                points=[
                    qmodels.PointStruct(
                        id=str(point_id),
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ChunkAdminService: Qdrant upsert failed")
            raise ChunkPersistenceError(
                f"Не удалось сохранить вектор в Qdrant: {exc}"
            ) from exc

    @staticmethod
    def _build_payload(
        text_id: int | None,
        source_id: int,
        region_codes: list[str],
        place_of_work: str | None,
        chunk_index: int,
        total_chunks: int,
    ) -> dict:
        return {
            "text_id": text_id,
            "source_id": source_id,
            "region_codes": region_codes or None,
            "place_of_work": place_of_work,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
        }
