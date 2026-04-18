from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.models import DocumentChunk
    from app.clients.base_clients import EmbeddingClient
    from app.repositories import DocumentRepository, ChunkRepository


class RAGService:
    _client: EmbeddingClient
    _document_rep: DocumentRepository
    _chunk_rep: ChunkRepository

    def __init__(
        self,
        client: EmbeddingClient,
        document_rep: DocumentRepository,
        chunk_rep: ChunkRepository,
    ) -> None:
        self._client = client
        self._document_rep = document_rep
        self._chunk_rep = chunk_rep

    async def retrieve(
        self, question: str, place_of_work: str | None = None
    ) -> list[DocumentChunk]:
        # TODO: Реализовать обработку превышения лимита токенов

        embeddings = await self._client.get_embeddings([question])

        doc_ids: set[int] = set()
        for embedding in embeddings:
            matches = await self._chunk_rep.search_similar_by_work(
                embedding, place_of_work
            )
            doc_ids.update(matches)

        return await self._document_rep.get_by_ids(list(doc_ids))
