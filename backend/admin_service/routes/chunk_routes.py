from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Form, Path, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from admin_service.core.templating import templates
from admin_service.dependencies.auth import CurrentAdminUnlockedDep
from admin_service.dependencies.config import AdminConfigDep
from admin_service.dependencies.services import ChunkAdminServiceDep
from admin_service.services.chunk_admin_service import (
    ChunkPersistenceError,
    ChunkValidationError,
)


router = APIRouter(prefix="/chunks")


@router.get("", response_class=HTMLResponse, name="chunk_list")
async def list_chunks(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    source_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Response:
    offset = (page - 1) * per_page
    chunks, total = await service.list_paginated(
        source_id=source_id,
        search=search,
        limit=per_page,
        offset=offset,
    )
    sources = await service.list_sources()
    total_pages = (total + per_page - 1) // per_page if per_page else 1
    return templates.TemplateResponse(
        request,
        "chunks/list.html",
        {
            "admin": admin,
            "chunks": chunks,
            "sources": sources,
            "selected_source_id": source_id,
            "search": search or "",
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/new", response_class=HTMLResponse, name="chunk_new")
async def new_chunk_form(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    source_id: int | None = Query(default=None),
) -> Response:
    sources = await service.list_sources()
    return templates.TemplateResponse(
        request,
        "chunks/new.html",
        {
            "admin": admin,
            "sources": sources,
            "preselected_source_id": source_id,
            "error": None,
            "draft_text": "",
        },
    )


@router.post("", name="chunk_create")
async def create_chunk(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    config: AdminConfigDep,
    source_id: Annotated[int, Form(...)],
    text: Annotated[str, Form(...)],
) -> Response:
    try:
        chunk = await service.create(source_id=source_id, text=text, admin_id=admin.id)
    except (ChunkValidationError, ChunkPersistenceError) as exc:
        sources = await service.list_sources()
        return templates.TemplateResponse(
            request,
            "chunks/new.html",
            {
                "admin": admin,
                "sources": sources,
                "preselected_source_id": source_id,
                "error": str(exc),
                "draft_text": text,
            },
            status_code=400,
        )
    return RedirectResponse(
        url=config.url_for(f"/chunks/{chunk.id}"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{chunk_id}", response_class=HTMLResponse, name="chunk_edit")
async def edit_chunk(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    chunk_id: Annotated[int, Path(...)],
) -> Response:
    chunk = await service.get(chunk_id)
    if chunk is None:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": "Чанк не найден",
                "message": f"Чанк #{chunk_id} не существует.",
                "status_code": 404,
            },
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "chunks/edit.html",
        {
            "admin": admin,
            "chunk": chunk,
            "error": None,
        },
    )


@router.post("/{chunk_id}", name="chunk_update")
async def update_chunk(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    config: AdminConfigDep,
    chunk_id: Annotated[int, Path(...)],
    text: Annotated[str, Form(...)],
) -> Response:
    try:
        await service.update(chunk_id=chunk_id, text=text, admin_id=admin.id)
    except KeyError:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": "Чанк не найден",
                "message": f"Чанк #{chunk_id} не существует.",
                "status_code": 404,
            },
            status_code=404,
        )
    except (ChunkValidationError, ChunkPersistenceError) as exc:
        chunk = await service.get(chunk_id)
        return templates.TemplateResponse(
            request,
            "chunks/edit.html",
            {
                "admin": admin,
                "chunk": chunk,
                "error": str(exc),
                "draft_text": text,
            },
            status_code=400,
        )
    return RedirectResponse(
        url=config.url_for(f"/chunks/{chunk_id}?saved=1"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{chunk_id}/delete", name="chunk_delete")
async def delete_chunk(
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    config: AdminConfigDep,
    chunk_id: Annotated[int, Path(...)],
) -> Response:
    try:
        await service.delete(chunk_id=chunk_id, admin_id=admin.id)
    except ChunkPersistenceError:
        # Persistence error already audited; re-render the edit page later
        return RedirectResponse(
            url=config.url_for(f"/chunks/{chunk_id}?delete_failed=1"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        url=config.url_for("/chunks"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
