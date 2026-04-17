from worker.repositories.vector_repository import VectorRepository
from worker.repositories.chunk_repository import ChunkRepository
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
        chunk_stored = self._chunk_rep.create_many(chunks)

        return chunk_stored

    def save_vectors(
        self,
        source_id: int,
        embedded_chunks: list[EmbeddedDocumentChunk],
        regions: list[str],
        place_of_work: str | None = None,
    ) -> int:
        self._vector_rep.delete_by_source_id(source_id)
        return self._vector_rep.upsert_chunks(embedded_chunks, regions, place_of_work)
