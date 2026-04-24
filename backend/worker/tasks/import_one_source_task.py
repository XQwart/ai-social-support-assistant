from __future__ import annotations

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies
from worker.dependencies.runtime import AsyncRuntime


async def _run_import_one_source(
    deps: WorkerDependencies,
    job: dict,
) -> dict:
    async with deps.session_scope() as session:
        service = deps.build_region_source_import_service(session=session)
        return await service.import_one_source(
            url=job["url"],
            region_name=job.get("region_name"),
            region_code=job.get("region_code"),
            place_of_work=job.get("place_of_work"),
        )


@app.task(bind=True, name="worker.tasks.import_one_source_task.import_one_source")
def import_one_source(self, job: dict) -> dict:
    runtime = AsyncRuntime.get()
    return runtime.run(_run_import_one_source(runtime.deps, job))
