from __future__ import annotations


from worker.schemas.document import StoredDocumentChunk, EmbeddedChunkForIndex
from worker.services.embedding.embedding_service import EmbeddingService
from worker.services.quests_service import ChunkQuestionLLMService


class ChunkIndexingService:
    def __init__(
        self,
        *,
        embedding_service: EmbeddingService,
        quest_service: ChunkQuestionLLMService,
    ) -> None:
        self._embeddings = embedding_service
        self._quest_service = quest_service

    async def prepare_index_data(
        self,
        stored_chunks: list[StoredDocumentChunk],
    ) -> list[EmbeddedChunkForIndex]:
        if not stored_chunks:
            return []

        chunks_with_questions = await self._quest_service.generate_for_chunks(
            stored_chunks
        )

        embedded_chunks = await self._embeddings.create_chunk_index_embeddings(
            chunks_with_questions
        )
        del chunks_with_questions

        return embedded_chunks
