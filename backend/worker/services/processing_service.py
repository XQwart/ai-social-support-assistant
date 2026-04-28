from __future__ import annotations

import logging

from worker.services.parsing.parsing_service import DocumentParsingService
from worker.services.document_service import DocumentService
from worker.services.embedding.embedding_service import EmbeddingService
from worker.services.chunk_service import ChunkingService
from worker.services.source.source_crawl_service import SourceCrawlService
from worker.services.quests_service import ChunkQuestionLLMService

logger = logging.getLogger(__name__)


class SourceProcessingService:
    def __init__(
        self,
        parsing_service: DocumentParsingService,
        document_service: DocumentService,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService,
        quest_service: ChunkQuestionLLMService,
        source_service: SourceCrawlService,
    ) -> None:
        self._parsing = parsing_service
        self._documents = document_service
        self._embeddings = embedding_service
        self._chunking = chunking_service
        self._sources = source_service
        self._quest_service = quest_service

    async def process_source(self, source: dict) -> dict:
        source_id = source["id"]
        url = source["url"]
        name = source["name"]
        document_type = source["document_type"]
        place_of_work = source["place_of_work"]

        try:
            result = await self._do_process(
                source_id=source_id,
                url=url,
                name=name,
                document_type=document_type,
                place_of_work=place_of_work,
            )
        except Exception as e:
            error_msg = str(e)
            e.__traceback__ = None
            logger.exception("Ошибка обработки source_id=%s", source_id)
            await self._sources.mark_failed(source_id, error=error_msg)
            return {
                "source_id": source_id,
                "status": "failed",
                "error": str(e),
            }

        await self._sources.mark_success(source_id)
        return result

    async def _do_process(
        self,
        source_id: int,
        url: str,
        name: str | None,
        document_type: str,
        place_of_work: str | None = None,
    ) -> dict:
        document = await self._parsing.parse_source(
            source_id=source_id,
            url=url,
            name=name,
            document_type=document_type,
        )

        if not document:
            await self._sources.mark_failed(source_id, error="empty")
            return {
                "source_id": source_id,
                "status": "skipped",
                "reason": "empty",
            }

        chunks = self._chunking.split_document(document=document)
        del document

        stored_chunks = await self._documents.save_chunks(
            source_id=source_id,
            chunks=chunks,
        )

        chunks_count = len(chunks)
        del chunks

        embedded_chunks = await self._embeddings.create_embeddings(stored_chunks)

        regions = await self._sources.get_region_codes_by_source_id(
            source_id=source_id,
        )

        chunk_vectors_count = await self._documents.save_vectors(
            source_id=source_id,
            embedded_chunks=embedded_chunks,
            regions=regions,
            place_of_work=place_of_work,
        )
        del embedded_chunks
        generated_questions = await self._quest_service.generate_for_chunks(
            stored_chunks,
        )
        del stored_chunks
        generated_questions_count = len(generated_questions)

        question_vectors_count = 0
        if generated_questions:
            embedded_questions = await self._embeddings.create_question_embeddings(
                generated_questions
            )
            del generated_questions

            question_vectors_count = await self._documents.save_question_vectors(
                source_id=source_id,
                embedded_questions=embedded_questions,
                regions=regions,
                place_of_work=place_of_work,
            )
            del embedded_questions

        return {
            "source_id": source_id,
            "url": url,
            "status": "success",
            "chunks_count": chunks_count,
            "chunk_vectors_count": chunk_vectors_count or 0,
            "questions_count": generated_questions_count,
            "question_vectors_count": question_vectors_count or 0,
        }
