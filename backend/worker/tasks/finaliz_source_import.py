from __future__ import annotations

import asyncio

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies


async def _run_finalize_source_import(results: list[dict]) -> dict:
    deps = await WorkerDependencies.get()

    try:
        async with deps.session_scope() as session:
            service = deps.build_region_source_import_service(session=session)
            result = service.aggregate_results(results)

        deps.runtime_state_service.set_sources_status("ready")
        return result

    except Exception:
        deps.runtime_state_service.set_sources_status("failed")
        raise


@app.task(
    bind=True, name="worker.tasks.finalize_source_import_task.finalize_source_import"
)
def finalize_source_import(self, results: list[dict]) -> dict:
    return asyncio.run(_run_finalize_source_import(results))
