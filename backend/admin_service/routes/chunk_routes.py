from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Form, Path, Query, Request, status
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)

from admin_service.core.templating import templates
from admin_service.dependencies.auth import CurrentAdminUnlockedDep
from admin_service.dependencies.config import AdminConfigDep
from admin_service.dependencies.services import ChunkAdminServiceDep
from admin_service.services.chunk_admin_service import (
    ChunkPersistenceError,
    ChunkValidationError,
)


router = APIRouter(prefix="/chunks")


def _parse_optional_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError as exc:
        raise ChunkValidationError(
            f"Некорректный идентификатор источника: {value!r}"
        ) from exc


def _normalize_form_str(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


async def _selected_source_preview(service, source_id: int | None) -> dict | None:
    if source_id is None:
        return None
    source = await service.get_source(source_id)
    if source is None:
        return None
    return {
        "id": source.id,
        "name": source.name or source.url,
        "url": source.url,
    }


async def _form_context(
    service, request: Request, source_id: int | None
) -> dict:
    regions = await service.list_regions()
    places = await service.list_places_of_work()
    selected_source = await _selected_source_preview(service, source_id)
    default_place: str | None = None
    default_region_code: str | None = None
    default_source_url: str | None = None
    if source_id is not None:
        source = await service.get_source(source_id)
        if source is not None:
            default_place = source.place_of_work
            default_source_url = source.url
            codes = await service.get_source_region_codes(source_id)
            default_region_code = codes[0] if codes else None
    return {
        "regions": regions,
        "places_of_work": places,
        "selected_source": selected_source,
        "default_place_of_work": default_place,
        "default_region_code": default_region_code,
        "default_source_url": default_source_url,
    }


@router.get("/sources/search", name="chunk_sources_search")
async def search_sources(
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> Response:
    offset = (page - 1) * per_page
    sources, total = await service.list_sources_paginated(
        search=_normalize_form_str(q),
        limit=per_page,
        offset=offset,
    )
    total_pages = (total + per_page - 1) // per_page if per_page else 1
    return JSONResponse(
        {
            "items": [
                {"id": s.id, "name": s.name or s.url, "url": s.url}
                for s in sources
            ],
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        }
    )


@router.get("", response_class=HTMLResponse, name="chunk_list")
async def list_chunks(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    source_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Response:
    parsed_source_id = _parse_optional_int(source_id)
    offset = (page - 1) * per_page
    chunks, total = await service.list_paginated(
        source_id=parsed_source_id,
        search=_normalize_form_str(search),
        limit=per_page,
        offset=offset,
    )
    selected_source = await _selected_source_preview(service, parsed_source_id)
    total_pages = (total + per_page - 1) // per_page if per_page else 1
    return templates.TemplateResponse(
        request,
        "chunks/list.html",
        {
            "admin": admin,
            "chunks": chunks,
            "selected_source_id": parsed_source_id,
            "selected_source": selected_source,
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
    source_id: str | None = Query(default=None),
) -> Response:
    parsed_source_id = _parse_optional_int(source_id)
    ctx = await _form_context(service, request, parsed_source_id)
    return templates.TemplateResponse(
        request,
        "chunks/new.html",
        {
            "admin": admin,
            "preselected_source_id": parsed_source_id,
            "error": None,
            "draft_text": "",
            "draft_region_code": ctx["default_region_code"],
            "draft_place_of_work": ctx["default_place_of_work"],
            "draft_source_url": ctx["default_source_url"],
            **ctx,
        },
    )


@router.post("", name="chunk_create")
async def create_chunk(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: ChunkAdminServiceDep,
    config: AdminConfigDep,
    text: Annotated[str, Form(...)],
    source_id: Annotated[str | None, Form()] = None,
    region_code: Annotated[str | None, Form()] = None,
    place_of_work: Annotated[str | None, Form()] = None,
    place_of_work_set: Annotated[str | None, Form()] = None,
    source_url: Annotated[str | None, Form()] = None,
) -> Response:
    parsed_source_id = _parse_optional_int(source_id)
    region_value = _normalize_form_str(region_code)
    source_url_value = _normalize_form_str(source_url)
    place_value = (place_of_work or "").strip()
    is_place_set = place_of_work_set == "1"

    try:
        result = await service.create(
            source_id=parsed_source_id,
            text=text,
            admin_id=admin.id,
            region_code=region_value,
            place_of_work=place_value,
            place_of_work_set=is_place_set,
            source_url=source_url_value,
        )
    except (ChunkValidationError, ChunkPersistenceError) as exc:
        ctx = await _form_context(service, request, parsed_source_id)
        return templates.TemplateResponse(
            request,
            "chunks/new.html",
            {
                "admin": admin,
                "preselected_source_id": parsed_source_id,
                "error": str(exc),
                "draft_text": text,
                "draft_region_code": region_value or ctx["default_region_code"],
                "draft_place_of_work": (
                    place_value if is_place_set else ctx["default_place_of_work"]
                ),
                "draft_source_url": (
                    source_url_value or ctx["default_source_url"]
                ),
                **ctx,
            },
            status_code=400,
        )
    target_source_id = result.get("source_id") or parsed_source_id
    list_url = "/chunks?created=1"
    if target_source_id:
        list_url = f"/chunks?source_id={target_source_id}&created=1"
    return RedirectResponse(
        url=config.url_for(list_url),
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
    ctx = await _form_context(service, request, chunk.source_id)
    return templates.TemplateResponse(
        request,
        "chunks/edit.html",
        {
            "admin": admin,
            "chunk": chunk,
            "error": None,
            **ctx,
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
    place_of_work: Annotated[str | None, Form()] = None,
    place_of_work_set: Annotated[str | None, Form()] = None,
) -> Response:
    place_value = (place_of_work or "").strip()
    is_place_set = place_of_work_set == "1"

    try:
        await service.update(
            chunk_id=chunk_id,
            text=text,
            admin_id=admin.id,
            place_of_work=place_value,
            place_of_work_set=is_place_set,
        )
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
        ctx = await _form_context(
            service, request, chunk.source_id if chunk else None
        )
        return templates.TemplateResponse(
            request,
            "chunks/edit.html",
            {
                "admin": admin,
                "chunk": chunk,
                "error": str(exc),
                "draft_text": text,
                "draft_place_of_work": place_value if is_place_set else None,
                **ctx,
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
        return RedirectResponse(
            url=config.url_for(f"/chunks/{chunk_id}?delete_failed=1"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        url=config.url_for("/chunks"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
