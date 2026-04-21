from __future__ import annotations
from typing import TYPE_CHECKING

from app.core.constants import is_sber_employee_place_of_work
from app.schemas.rag_schemas import RetrievedChunk

if TYPE_CHECKING:
    from langchain_core.embeddings.embeddings import Embeddings

    from app.repositories import DocumentRepository, ChunkRepository


class RAGService:
    _client: Embeddings
    _document_rep: DocumentRepository
    _chunk_rep: ChunkRepository

    def __init__(
        self,
        client: Embeddings,
        document_rep: DocumentRepository,
        chunk_rep: ChunkRepository,
    ) -> None:
        self._client = client
        self._document_rep = document_rep
        self._chunk_rep = chunk_rep

    async def retrieve(
        self,
        question: str,
        region: str | None,
        place_of_work: str | None = None,
    ) -> list[RetrievedChunk]:
        embeddings = await self._client.aembed_documents([question])

        place_by_id: dict[int, str | None] = {}
        for embedding in embeddings:
            matches = await self._chunk_rep.search_similar_by_work(
                embedding, region, place_of_work
            )
            for doc_id, chunk_place_of_work in matches:
                place_by_id.setdefault(doc_id, chunk_place_of_work)

        if not place_by_id:
            return []

        documents = await self._document_rep.get_by_ids(list(place_by_id.keys()))

        return [
            RetrievedChunk(
                source_name=doc.source_name,
                source_url=doc.source_url,
                text=doc.text,
                is_internal=is_sber_employee_place_of_work(place_by_id.get(doc.id)),
            )
            for doc in documents
        ]
