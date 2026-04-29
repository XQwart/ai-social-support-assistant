from __future__ import annotations

import logging

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies
from worker.dependencies.runtime import AsyncRuntime

logger = logging.getLogger(__name__)


async def _run_update_knowledge(
    deps: WorkerDependencies,
    source: dict,
) -> dict:
    async with deps.session_scope() as session:
        service = deps.build_processing_service(session=session)
        return await service.process_source(source)


@app.task(bind=True, name="worker.tasks.update_knowledge.update_knowledge")
def update_knowledge(self, source: dict) -> dict:
    runtime = AsyncRuntime.get()
    return runtime.run(_run_update_knowledge(runtime.deps, source))
