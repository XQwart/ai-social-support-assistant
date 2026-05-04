from __future__ import annotations

import logging

from worker.celery_app import app
from worker.dependencies.runtime import AsyncRuntime

logger = logging.getLogger(__name__)


async def _run_update_knowledge(source: dict) -> dict:
    deps = AsyncRuntime.get().deps
    source_id = source["id"]

    async with deps.session_scope() as session:
        source_service = deps.build_source_crawl_service(session)

        try:
            document = await deps.parsing_service.parse_source(
                source_id=source_id,
                url=source["url"],
                name=source["name"],
                document_type=source["document_type"],
                place_of_work=source["place_of_work"],
            )

            if not document:
                await source_service.mark_failed(source_id, error="empty")
                return {"source_id": source_id, "status": "skipped"}

            resp = await deps.http_client.post(
                f"{deps.processing_url}/api/v1/source",
                json=document.model_dump(),
            )
            resp.raise_for_status()
            result = resp.json()

            await source_service.mark_success(source_id)
            return result

        except Exception as e:
            logger.exception("Ошибка source_id=%s", source_id)
            await source_service.mark_failed(source_id, error=str(e))
            return {"source_id": source_id, "status": "failed", "error": str(e)}


@app.task(bind=True, name="worker.tasks.update_knowledge.update_knowledge")
def update_knowledge(self, source: dict) -> dict:
    runtime = AsyncRuntime.get()
    return runtime.run(_run_update_knowledge(source))
