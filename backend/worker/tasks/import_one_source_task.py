from __future__ import annotations

from sqlalchemy.exc import DBAPIError

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies
from worker.dependencies.runtime import AsyncRuntime


DEADLOCK_SQLSTATE = "40P01"


def _is_deadlock_error(exc: BaseException) -> bool:
    current: BaseException | None = exc

    while current is not None:
        sqlstate = getattr(current, "sqlstate", None)
        pgcode = getattr(current, "pgcode", None)

        if sqlstate == DEADLOCK_SQLSTATE or pgcode == DEADLOCK_SQLSTATE:
            return True

        current = current.__cause__

    message = str(exc).lower()
    return (
        "deadlock detected" in message
        or "deadlockdetectederror" in message
        or DEADLOCK_SQLSTATE.lower() in message
    )


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


@app.task(
    bind=True,
    name="worker.tasks.import_one_source_task.import_one_source",
    max_retries=5,
)
def import_one_source(self, job: dict) -> dict:
    runtime = AsyncRuntime.get()

    try:
        return runtime.run(_run_import_one_source(runtime.deps, job))

    except DBAPIError as exc:
        if _is_deadlock_error(exc):
            countdown = min(60, 2**self.request.retries)

            raise self.retry(
                exc=exc,
                countdown=countdown,
            )

        raise
