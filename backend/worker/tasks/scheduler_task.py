from __future__ import annotations

from datetime import datetime, timedelta, timezone

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies
from worker.dependencies.runtime import AsyncRuntime
from worker.services.sheduler_service import SchedulerService


async def _run_dispatch_due_crawls(deps: WorkerDependencies) -> dict:
    async with deps.session_scope() as session:
        source_service = deps.build_source_crawl_service(session)
        service = SchedulerService(source_service=source_service)
        return await service.dispatch_due_crawls()


async def _run_reap_stale_locks(deps: WorkerDependencies) -> dict:
    async with deps.session_scope() as session:
        source_service = deps.build_source_crawl_service(session)

        threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
        released_count = await source_service.release_stale_locks(
            threshold=threshold,
        )

        return {
            "status": "success",
            "released_count": released_count,
            "threshold": threshold.isoformat(),
        }


@app.task(bind=True, name="worker.tasks.scheduler_task.dispatch_due_crawls")
def dispatch_due_crawls(self) -> dict:
    runtime = AsyncRuntime.get()
    return runtime.run(_run_dispatch_due_crawls(runtime.deps))


@app.task(bind=True, name="worker.tasks.scheduler_task.reap_stale_locks")
def reap_stale_locks(self) -> dict:
    runtime = AsyncRuntime.get()
    return runtime.run(_run_reap_stale_locks(runtime.deps))
