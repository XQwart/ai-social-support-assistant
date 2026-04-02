from datetime import timezone, timedelta, datetime
from worker.celery_app import app
from worker.services.sheduler_service import SchedulerService
from worker.repositories.source import SourceRepository
from worker.dependencies.build import WorkerDependencies


@app.task(name="worker.tasks.scheduler.dispatch_due_crawls")
def dispatch_due_crawls() -> dict:
    deps = WorkerDependencies.get()

    with deps.session_scope() as session:
        source_rep = SourceRepository(session=session)
        service = SchedulerService(source_repository=source_rep)
        return service.dispatch_due_crawls()


@app.task(name="worker.tasks.scheduler.reap_stale_locks")
def reap_stale_locks() -> dict:
    deps = WorkerDependencies.get()

    with deps.session_scope() as session:
        source_rep = SourceRepository(session=session)
        threshold = datetime.now(timezone.utc) - timedelta(
            minutes=30,
        )
        released_count = source_rep.release_stale_locks(threshold=threshold)

        return {
            "status": "success",
            "released_count": released_count,
            "threshold": threshold.isoformat(),
        }
