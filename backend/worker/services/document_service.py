from __future__ import annotations

from worker.repositories.vector_repository import VectorRepository
from worker.repositories.chunk_repository import ChunkRepository
from worker.schemas.document import (
    DocumentChunkCreate,
    StoredDocumentChunk,
    EmbeddedDocumentChunk,
    EmbeddedChunkQuestion,
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

    async def save_vectors(
        self,
        source_id: int,
        embedded_chunks: list[EmbeddedDocumentChunk],
        regions: list[str],
        place_of_work: str | None = None,
    ) -> int:
        await self._vector_rep.delete_chunks_by_source_id(source_id)
        return await self._vector_rep.upsert_chunks(
            embedded_chunks,
            regions,
            place_of_work,
        )

    async def save_question_vectors(
        self,
        source_id: int,
        embedded_questions: list[EmbeddedChunkQuestion],
        regions: list[str],
        place_of_work: str | None = None,
    ) -> int:
        await self._vector_rep.delete_questions_by_source_id(source_id)
        return await self._vector_rep.upsert_questions(
            embedded_questions,
            regions,
            place_of_work,
        )
