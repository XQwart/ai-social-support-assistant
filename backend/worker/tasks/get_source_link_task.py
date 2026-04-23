from __future__ import annotations

from celery import chord

from worker.celery_app import app
from worker.core.constants import SOURCES_JSON
from worker.tasks.import_one_source import import_one_source
from worker.tasks.finaliz_source_import import finalize_source_import
from worker.utils.read_json import read_json_file, build_source_jobs


@app.task(bind=True, name="worker.tasks.get_source_link_task.get_source_links")
def get_source_links(self) -> dict:
    from worker.dependencies.build import WorkerDependencies
    import asyncio

    async def _run() -> dict:
        deps = await WorkerDependencies.get()
        sources = read_json_file(SOURCES_JSON)
        jobs = build_source_jobs(sources)

        if not jobs:
            return {
                "status": "noop",
                "scheduled_count": 0,
                "message": "No sources found",
            }

        deps.runtime_state_service.set_sources_status("running")

        chord(
            (import_one_source.s(job) for job in jobs),
            finalize_source_import.s(),
        ).apply_async()

        return {
            "status": "scheduled",
            "scheduled_count": len(jobs),
        }

    return asyncio.run(_run())
