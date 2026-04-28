from __future__ import annotations

from sqlalchemy.exc import DBAPIError

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies
from worker.dependencies.runtime import AsyncRuntime


def _is_deadlock_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return "deadlock detected" in message or "40p01" in message


async def _run_add_text_to_source(
    deps: WorkerDependencies,
    job: dict,
) -> dict:
    async with deps.session_scope() as session:
        service = deps.build_chunk_management_service(session=session)

        return await service.add_text_to_source(
            source_url=job["source_url"],
            source_name=job.get("source_name"),
            region_code=job.get("region_code"),
            region_name=job.get("region_name"),
            place_of_work=job.get("place_of_work"),
            text=job["text"],
        )


async def _run_update_chunk(
    deps: WorkerDependencies,
    job: dict,
) -> dict:
    async with deps.session_scope() as session:
        service = deps.build_chunk_management_service(session=session)

        return await service.update_chunk(
            chunk_id=job["chunk_id"],
            text=job["text"],
            place_of_work=job.get("place_of_work"),
        )


async def _run_delete_chunk(
    deps: WorkerDependencies,
    job: dict,
) -> dict:
    async with deps.session_scope() as session:
        service = deps.build_chunk_management_service(session=session)

        return await service.delete_chunk(
            chunk_id=job["chunk_id"],
        )


@app.task(
    bind=True,
    name="worker.tasks.chunk_management.add_text_to_source",
    max_retries=5,
)
def add_text_to_source(self, job: dict) -> dict:
    runtime = AsyncRuntime.get()

    try:
        return runtime.run(_run_add_text_to_source(runtime.deps, job))

    except DBAPIError as exc:
        if _is_deadlock_error(exc):
            raise self.retry(
                exc=exc,
                countdown=min(60, 2**self.request.retries),
            )

        raise


@app.task(
    bind=True,
    name="worker.tasks.chunk_management.update_chunk",
    max_retries=5,
)
def update_chunk(self, job: dict) -> dict:
    runtime = AsyncRuntime.get()

    try:
        return runtime.run(_run_update_chunk(runtime.deps, job))

    except DBAPIError as exc:
        if _is_deadlock_error(exc):
            raise self.retry(
                exc=exc,
                countdown=min(60, 2**self.request.retries),
            )

        raise


@app.task(
    bind=True,
    name="worker.tasks.chunk_management.delete_chunk",
    max_retries=5,
)
def delete_chunk(self, job: dict) -> dict:
    runtime = AsyncRuntime.get()

    try:
        return runtime.run(_run_delete_chunk(runtime.deps, job))

    except DBAPIError as exc:
        if _is_deadlock_error(exc):
            raise self.retry(
                exc=exc,
                countdown=min(60, 2**self.request.retries),
            )

        raise
