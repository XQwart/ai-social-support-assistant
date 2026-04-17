import logging

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies

logger = logging.getLogger(__name__)


@app.task(bind=True, name="worker.tasks.update_knowledge.update_knowledge")
def update_knowledge(self, source: dict) -> dict:
    deps = WorkerDependencies.get()

    with deps.session_scope() as session:
        service = deps.build_processing_service(session=session)
        result = service.process_source(source)
        return result
