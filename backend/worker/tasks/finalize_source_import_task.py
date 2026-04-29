from __future__ import annotations

from worker.celery_app import app
from worker.dependencies.runtime import AsyncRuntime
from worker.dependencies.build import WorkerDependencies


async def _run_finalize_source_import(
    deps: WorkerDependencies,
    results: list[dict],
) -> dict:
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
    bind=True,
    name="worker.tasks.finalize_source_import_task.finalize_source_import",
)
def finalize_source_import(self, results: list[dict]) -> dict:
    runtime = AsyncRuntime.get()
    return runtime.run(_run_finalize_source_import(runtime.deps, results))
