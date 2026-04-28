from __future__ import annotations

from fastapi import APIRouter, status

from worker.celery_app import app
from worker.schemas.request import AddTextToSourceRequest, UpdateChunkRequest


router = APIRouter(
    prefix="/api/v1",
    tags=["chunks"],
)


@router.post("/sources/text", status_code=status.HTTP_202_ACCEPTED)
async def add_text(payload: AddTextToSourceRequest) -> dict:
    task = app.send_task(
        "worker.tasks.chunk_management.add_text_to_source",
        args=[payload.model_dump()],
        queue="default",
        priority=0,
    )

    return {
        "status": "accepted",
        "task_id": task.id,
    }


@router.patch("/chunks/{chunk_id}", status_code=status.HTTP_202_ACCEPTED)
async def patch_chunk(chunk_id: int, payload: UpdateChunkRequest) -> dict:
    task = app.send_task(
        "worker.tasks.chunk_management.update_chunk",
        args=[
            {
                "chunk_id": chunk_id,
                "text": payload.text,
                "place_of_work": payload.place_of_work,
            }
        ],
        queue="default",
        priority=0,
    )

    return {
        "status": "accepted",
        "task_id": task.id,
    }


@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_202_ACCEPTED)
async def remove_chunk(chunk_id: int) -> dict:
    task = app.send_task(
        "worker.tasks.chunk_management.delete_chunk",
        args=[
            {
                "chunk_id": chunk_id,
            }
        ],
        queue="default",
        priority=0,
    )

    return {
        "status": "accepted",
        "task_id": task.id,
    }
