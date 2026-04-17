from __future__ import annotations

import logging

from worker.services.parsing.parsing_service import DocumentParsingService
from worker.services.document_service import DocumentService
from worker.services.embedding.embedding_service import EmbeddingService
from worker.services.chunk_service import ChunkingService
from worker.services.source.source_crawl_service import SourceCrawlService

logger = logging.getLogger(__name__)


class SourceProcessingService:
    def __init__(
        self,
        parsing_service: DocumentParsingService,
        document_service: DocumentService,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService,
        source_service: SourceCrawlService,
    ) -> None:
        self._parsing = parsing_service
        self._documents = document_service
        self._embeddings = embedding_service
        self._chunking = chunking_service
        self._sources = source_service

    def process_source(self, source: dict) -> dict:
        source_id = source["id"]
        url = source["url"]
        name = source["name"]
        document_type = source["document_type"]
        place_of_work = source["place_of_work"]
        try:
            result = self._do_process(
                source_id=source_id,
                url=url,
                name=name,
                document_type=document_type,
                place_of_work=place_of_work,
            )

        except Exception as e:
            logger.exception("Ошибка обработки source_id=%s", source_id)
            self._sources.mark_failed(source_id, error=str(e))
            return {
                "source_id": source_id,
                "status": "failed",
                "error": str(e),
            }

        self._sources.mark_success(source_id)
        return result

    def _do_process(
        self,
        source_id: int,
        url: str,
        name: str | None,
        document_type: str,
        place_of_work: str | None = None,
    ) -> dict:
        document = self._parsing.parse_source(
            source_id=source_id, url=url, name=name, document_type=document_type
        )

        if not document:
            self._sources.mark_failed(source_id, error="empty")
            return {
                "source_id": source_id,
                "status": "skipped",
                "reason": "empty",
            }

        chunks = self._chunking.split_document(document=document)
        stored_chunks = self._documents.save_chunks(
            source_id=source_id,
            chunks=chunks,
        )

        embedded_chunks = self._embeddings.create_embeddings(stored_chunks)
        regions = self._sources.get_region_codes_by_source_id(source_id=source_id)

        vectors_count = self._documents.save_vectors(
            source_id=source_id,
            embedded_chunks=embedded_chunks,
            regions=regions,
            place_of_work=place_of_work,
        )

        return {
            "source_id": source_id,
            "url": url,
            "status": "success",
            "chunks_count": len(chunks),
            "vectors_count": vectors_count or 0,
        }
