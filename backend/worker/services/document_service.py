from __future__ import annotations

from collections.abc import Sequence
from shared.schemas.document_type import AccessScope, GeoScope
from worker.repositories.vector_repository import VectorRepository
from worker.repositories.chunk_repository import ChunkRepository
from worker.schemas.document import (
    DocumentChunkCreate,
    StoredDocumentChunk,
    EmbeddedChunkForIndex,
)


class DocumentService:
    _vector_rep: VectorRepository
    _chunk_rep: ChunkRepository

    def __init__(
        self,
        vector_rep: VectorRepository,
        chunk_rep: ChunkRepository,
    ) -> None:
        self._vector_rep = vector_rep
        self._chunk_rep = chunk_rep

    async def save_chunks(
        self,
        source_id: int,
        chunks: list[DocumentChunkCreate],
    ) -> list[StoredDocumentChunk]:
        await self._chunk_rep.delete_by_source_id(source_id)
        return await self._chunk_rep.create_many(chunks)

    async def create_chunks(
        self,
        chunks: Sequence[DocumentChunkCreate],
    ) -> list[StoredDocumentChunk]:
        return await self._chunk_rep.create_many(chunks)

    async def get_chunks_by_ids(
        self,
        chunk_ids: Sequence[int],
    ) -> list[StoredDocumentChunk]:
        return await self._chunk_rep.get_by_ids(chunk_ids)

    async def get_next_chunk_index(
        self,
        source_id: int,
    ) -> int:
        return await self._chunk_rep.get_next_chunk_index(source_id)

    async def update_chunk_text(
        self,
        *,
        chunk_id: int,
        text: str,
    ) -> StoredDocumentChunk:
        return await self._chunk_rep.update_text(
            chunk_id=chunk_id,
            text=text,
        )

    async def delete_chunk_by_id(
        self,
        chunk_id: int,
    ) -> int:
        return await self._chunk_rep.delete_by_id(chunk_id)

    async def upsert_chunk_vectors(
        self,
        chunks: Sequence[EmbeddedChunkForIndex],
        regions: list[str],
        access_scope: AccessScope,
        geo_scope: GeoScope,
        place_of_work: str | None = None,
    ) -> int:
        if not chunks:
            return 0

        return await self._vector_rep.upsert_chunks(
            embedded_chunks=chunks,
            regions=regions,
            access_scope=access_scope,
            geo_scope=geo_scope,
            place_of_work=place_of_work,
        )

    async def delete_index_data_by_chunk_id(
        self,
        chunk_id: int,
    ) -> None:
        await self._vector_rep.delete_chunk_by_chunk_id(chunk_id)

    async def delete_index_data_by_source_id(
        self,
        source_id: int,
    ) -> None:
        await self._vector_rep.delete_chunks_by_source_id(source_id)
