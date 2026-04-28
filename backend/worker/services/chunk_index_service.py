from __future__ import annotations


from worker.schemas.document import StoredDocumentChunk, PreparedChunkIndex
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
    ) -> PreparedChunkIndex:
        if not stored_chunks:
            return PreparedChunkIndex(
                embedded_chunks=[],
                generated_questions=[],
                embedded_questions=[],
            )

        embedded_chunks = await self._embeddings.create_embeddings(stored_chunks)

        generated_questions = await self._quest_service.generate_for_chunks(
            stored_chunks
        )

        if generated_questions:
            embedded_questions = await self._embeddings.create_question_embeddings(
                generated_questions
            )
        else:
            embedded_questions = []

        return PreparedChunkIndex(
            embedded_chunks=embedded_chunks,
            generated_questions=generated_questions,
            embedded_questions=embedded_questions,
        )
