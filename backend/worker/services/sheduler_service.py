from uuid import uuid4
from worker.tasks.update_knowledge_task import update_knowledge
from celery import group
from worker.services.source_service import SourceService


class SchedulerService:
    _source_service: SourceService

    def __init__(self, source_service: SourceService):
        self._source_service = source_service

    def dispatch_due_crawls(self) -> dict:

        sources = self._source_service.claim_due_sources(
            limit=50,
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
            }
            for source in sources
        ]

        batch_id = str(uuid4())

        source_ids = [payload["id"] for payload in source_payloads]

        group(
            update_knowledge.s(source_payload) for source_payload in source_payloads
        ).apply_async()

        return {
            "status": "scheduled",
            "scheduled_count": len(source_ids),
            "batch_id": batch_id,
            "source_ids": source_ids,
        }
