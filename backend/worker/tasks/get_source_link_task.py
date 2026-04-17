import logging

from worker.celery_app import app
from worker.dependencies.build import WorkerDependencies
from worker.core.constants import SOURCES_JSON
from worker.utils.read_json import read_json_file

logger = logging.getLogger(__name__)


@app.task(bind=True, name="worker.tasks.get_source_link_task.get_source_links")
def get_source_links(self) -> dict:
    deps = WorkerDependencies.get()
    sources = read_json_file(SOURCES_JSON)

    with deps.session_scope() as session:
        service = deps.build_region_source_import_service(session=session)

        result = service.import_from_data(sources=sources)

        return result
