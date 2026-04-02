from datetime import datetime, timezone
from uuid import uuid4
from worker.tasks.update_knowledge_task import update_knowledge
from celery import group
from worker.repositories.source import SourceRepository


class SchedulerService:
    _source_repository: SourceRepository

    def __init__(self, source_repository: SourceRepository):
        self._source_repository = source_repository

    def dispatch_due_crawls(self) -> dict:
        now = datetime.now(timezone.utc)

        sources = self._source_repository.claim_due_sources(
            now=now,
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
                "region": source.region,
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
