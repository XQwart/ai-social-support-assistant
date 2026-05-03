# app/routers/chunks.py
from __future__ import annotations

from fastapi import APIRouter, status

from worker.dependencies.services import ChunkManagementServiceDep
from worker.schemas.request import AddTextToSourceRequest, UpdateChunkRequest

router = APIRouter(
    prefix="/api/v1",
    tags=["chunks"],
)


@router.post("/chunks/text", status_code=status.HTTP_201_CREATED)
async def add_text(
    payload: AddTextToSourceRequest,
    chunk_manager: ChunkManagementServiceDep,
):
    return await chunk_manager.add_text_to_source(
        source_url=payload.source_url,
        source_name=payload.source_name,
        region_code=payload.region_code,
        region_name=payload.region_name,
        place_of_work=payload.place_of_work,
        text=payload.text,
    )


@router.patch("/chunks/{chunk_id}")
async def patch_chunk(
    chunk_id: int,
    payload: UpdateChunkRequest,
    chunk_manager: ChunkManagementServiceDep,
):
    return await chunk_manager.update_chunk(
        chunk_id=chunk_id,
        text=payload.text,
        place_of_work=payload.place_of_work,
    )


@router.delete("/chunks/{chunk_id}")
async def remove_chunk(
    chunk_id: int,
    chunk_manager: ChunkManagementServiceDep,
):
    return await chunk_manager.delete_chunk(chunk_id=chunk_id)
