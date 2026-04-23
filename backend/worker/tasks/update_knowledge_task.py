from __future__ import annotations

import asyncio
import logging

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies

logger = logging.getLogger(__name__)


async def _run_update_knowledge(source: dict) -> dict:
    deps = await WorkerDependencies.get()

    async with deps.session_scope() as session:
        service = deps.build_processing_service(session=session)
        result = await service.process_source(source)
        return result


@app.task(bind=True, name="worker.tasks.update_knowledge.update_knowledge")
def update_knowledge(self, source: dict) -> dict:
    return asyncio.run(_run_update_knowledge(source))
