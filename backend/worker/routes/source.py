from __future__ import annotations

from fastapi import APIRouter

from worker.dependencies.services import ChunkManagementServiceDep
from worker.schemas.document import ParsedDocument

router = APIRouter(
    prefix="/api/v1",
    tags=["sources"],
)


@router.post("/source", status_code=201)
async def add_source(
    source: ParsedDocument,
    chunk_manager: ChunkManagementServiceDep,
):
    result = await chunk_manager.ingest_document(document=source, replace_existing=True)
    return result
