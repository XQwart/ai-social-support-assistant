from __future__ import annotations

import logging

from worker.services.parsing.parsing_service import DocumentParsingService
from worker.services.source.source_crawl_service import SourceCrawlService
from worker.services.chunk_manager_service import ChunkManagementService

logger = logging.getLogger(__name__)


class SourceProcessingService:
    def __init__(
        self,
        parsing_service: DocumentParsingService,
        source_service: SourceCrawlService,
        chunk_management_service: ChunkManagementService,
    ) -> None:
        self._parsing = parsing_service
        self._sources = source_service
        self._chunk_management = chunk_management_service

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

            await self._sources.mark_failed(
                source_id,
                error=error_msg,
            )

            return {
                "source_id": source_id,
                "status": "failed",
                "error": error_msg,
            }

        await self._sources.mark_success(source_id)

        return result

    async def _do_process(
        self,
        *,
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
                "url": url,
                "status": "skipped",
                "reason": "empty",
            }

        result = await self._chunk_management.ingest_document(
            document=document,
            place_of_work=place_of_work,
            replace_existing=True,
        )

        del document

        return result
