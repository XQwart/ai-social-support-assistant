from __future__ import annotations

from datetime import datetime, timedelta, timezone

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies
from worker.dependencies.runtime import AsyncRuntime
from worker.repositories.source_crawl_repository import SourceCrawlRepository
from worker.services.sheduler_service import SchedulerService
from worker.services.source.source_crawl_service import SourceCrawlService


async def _run_dispatch_due_crawls(
    deps: WorkerDependencies,
) -> dict:
    if not deps.runtime_state_service.is_sources_ready():
        return {
            "status": "skipped",
            "reason": "source links are not initialized yet",
        }

    async with deps.session_scope() as session:
        source_rep = SourceCrawlRepository(session=session)
        source_service = SourceCrawlService(source_repository=source_rep)
        service = SchedulerService(source_service=source_service)
        return await service.dispatch_due_crawls()


async def _run_reap_stale_locks(
    deps: WorkerDependencies,
) -> dict:
    async with deps.session_scope() as session:
        source_rep = SourceCrawlRepository(session=session)
        source_service = SourceCrawlService(source_repository=source_rep)

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
