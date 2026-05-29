from __future__ import annotations

from celery import chord, signature

from worker.celery_app import app
from worker.core.constants import SOURCES_JSON
from worker.utils.read_json import read_json_file, build_source_jobs


@app.task(bind=True, name="worker.tasks.get_source_link_task.get_source_links")
def get_source_links(self) -> dict:

    sources = read_json_file(SOURCES_JSON)
    jobs = build_source_jobs(sources)

    if not jobs:
        return {
            "status": "noop",
            "scheduled_count": 0,
            "message": "No sources found",
        }

    chord(
        (
            signature(
                "worker.tasks.import_one_source_task.import_one_source",
                args=[job],
            )
            for job in jobs
        ),
        signature(
            "worker.tasks.finalize_source_import_task.finalize_source_import",
        ),
    ).apply_async()

    return {
        "status": "scheduled",
        "scheduled_count": len(jobs),
    }
