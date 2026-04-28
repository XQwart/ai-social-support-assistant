from uuid import uuid4
from celery import group, signature
from worker.services.source.source_crawl_service import SourceCrawlService


class SchedulerService:
    _source_service: SourceCrawlService

    def __init__(self, source_service: SourceCrawlService):
        self._source_service = source_service

    async def dispatch_due_crawls(self) -> dict:

        sources = await self._source_service.claim_due_sources(
            limit=500,
        )

        if not sources:
            return {
                "status": "noop",
                "scheduled_count": 0,
                "message": "No due sources found",
            }

        source_payloads = [
            {
                "id": source.id,
                "url": source.url,
                "name": source.name,
                "document_type": source.document_type,
                "place_of_work": source.place_of_work,
            }
            for source in sources
        ]

        batch_id = str(uuid4())

        source_ids = [payload["id"] for payload in source_payloads]

        group(
            signature(
                "worker.tasks.update_knowledge.update_knowledge",
                args=[source_payload],
            )
            for source_payload in source_payloads
        ).apply_async()

        return {
            "status": "scheduled",
            "scheduled_count": len(source_ids),
            "batch_id": batch_id,
            "source_ids": source_ids,
        }
