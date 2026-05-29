from __future__ import annotations
import difflib
from typing import Annotated

from fastapi import APIRouter, Form, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.agent.prompts import PROMPT_DESCRIPTIONS

from admin_service.core.templating import templates
from admin_service.dependencies.auth import CurrentAdminUnlockedDep
from admin_service.dependencies.config import AdminConfigDep
from admin_service.dependencies.services import PromptAdminServiceDep
from admin_service.services.prompt_admin_service import PromptValidationError


router = APIRouter(prefix="/prompts")


@router.get("", response_class=HTMLResponse, name="prompt_list")
async def list_prompts(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: PromptAdminServiceDep,
) -> Response:
    prompts = await service.list_all()
    return templates.TemplateResponse(
        request,
        "prompts/list.html",
        {
            "admin": admin,
            "prompts": prompts,
            "descriptions": PROMPT_DESCRIPTIONS,
        },
    )


@router.get("/{key}", response_class=HTMLResponse, name="prompt_edit")
async def edit_prompt(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: PromptAdminServiceDep,
    key: Annotated[str, Path(...)],
) -> Response:
    prompt = await service.get(key)
    if prompt is None:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": "Промпт не найден",
                "message": f"Ключ {key} не существует.",
                "status_code": 404,
            },
            status_code=404,
        )
    description = PROMPT_DESCRIPTIONS.get(key)
    return templates.TemplateResponse(
        request,
        "prompts/edit.html",
        {
            "admin": admin,
            "prompt": prompt,
            "description": description,
            "error": None,
            "saved": False,
        },
    )


@router.post("/{key}", name="prompt_save")
async def save_prompt(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: PromptAdminServiceDep,
    config: AdminConfigDep,
    key: Annotated[str, Path(...)],
    body: Annotated[str, Form(...)],
) -> Response:
    try:
        await service.update(key=key, new_body=body, admin_id=admin.id)
    except PromptValidationError as exc:
        prompt = await service.get(key)
        return templates.TemplateResponse(
            request,
            "prompts/edit.html",
            {
                "admin": admin,
                "prompt": prompt,
                "description": PROMPT_DESCRIPTIONS.get(key),
                "error": str(exc),
                "saved": False,
                "draft_body": body,
            },
            status_code=400,
        )
    except KeyError:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": "Промпт не найден",
                "message": f"Ключ {key} не существует.",
                "status_code": 404,
            },
            status_code=404,
        )

    return RedirectResponse(
        url=config.url_for(f"/prompts/{key}?saved=1"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/{key}/history",
    response_class=HTMLResponse,
    name="prompt_history",
)
async def prompt_history(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    service: PromptAdminServiceDep,
    key: Annotated[str, Path(...)],
) -> Response:
    current = await service.get(key)
    if current is None:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": "Промпт не найден",
                "message": f"Ключ {key} не существует.",
                "status_code": 404,
            },
            status_code=404,
        )
    history = await service.get_history(key)

    diffs = []
    for entry in history:
        diff_lines = list(
            difflib.unified_diff(
                entry.body.splitlines(),
                current.body.splitlines(),
                fromfile=f"v{entry.version}",
                tofile=f"v{current.version}",
                lineterm="",
            )
        )
        diffs.append(
            {
                "version": entry.version,
                "changed_at": entry.changed_at,
                "changed_by": entry.changed_by,
                "diff": "\n".join(diff_lines),
            }
        )

    return templates.TemplateResponse(
        request,
        "prompts/history.html",
        {
            "admin": admin,
            "prompt": current,
            "diffs": diffs,
        },
    )
