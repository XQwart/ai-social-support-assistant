from __future__ import annotations

import logging

from worker.services.parsing_service import ParsingService
from worker.services.document_service import DocumentService
from worker.services.embedding_service import EmbeddingService
from worker.services.chunk_service import ChunkingService
from worker.repositories.source import SourceRepository

logger = logging.getLogger(__name__)


class SourceProcessingService:
    def __init__(
        self,
        parsing_service: ParsingService,
        document_service: DocumentService,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService,
        source_rep: SourceRepository,
    ) -> None:
        self._parsing = parsing_service
        self._documents = document_service
        self._embeddings = embedding_service
        self._chunking = chunking_service
        self._sources = source_rep

    def process_source(self, source: dict) -> dict:
        source_id = source["id"]
        url = source["url"]
        region_code = source["region_code"]
        name = source["name"]

        try:
            result = self._do_process(
                source_id=source_id,
                url=url,
                region_code=region_code,
                name=name,
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

    def _do_process(self, source_id, url, region_code, name) -> dict:
        document = self._parsing.parse_source(
            source_id=source_id,
            url=url,
            region_code=region_code,
            name=name,
        )

        if not document:
            raise ValueError(f"Пустой контент: {url}")

        chunks = self._chunking.split_document(document=document)

        stored_chunks = self._documents.save_chunks(
            source_id=source_id,
            chunks=chunks,
        )

        embedded_chunks = self._embeddings.create_embeddings(stored_chunks)

        vectors_count = self._documents.save_vectors(
            source_id=source_id,
            embedded_chunks=embedded_chunks,
        )

        return {
            "source_id": source_id,
            "url": url,
            "region_code": region_code,
            "status": "success",
            "chunks_count": len(chunks),
            "vectors_count": vectors_count or 0,
        }
