from worker.repositories.vector_repositories import VectorRepository
from worker.repositories.chunk_repositories import ChunkRepository
from worker.schemas.document import (
    DocumentChunkCreate,
    StoredDocumentChunk,
    EmbeddedDocumentChunk,
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

    def save_chunks(
        self,
        source_id: int,
        chunks: list[DocumentChunkCreate],
    ) -> list[StoredDocumentChunk]:
        self._chunk_rep.delete_by_source_id(source_id)
        return self._chunk_rep.create_many(chunks)

    def save_vectors(
        self,
        source_id: int,
        embedded_chunks: list[EmbeddedDocumentChunk],
    ) -> int:
        self._vector_rep.delete_by_source_id(source_id)
        return self._vector_rep.upsert_chunks(embedded_chunks)
