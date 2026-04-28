from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Form, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from admin_service.core.templating import templates
from admin_service.dependencies.auth import CurrentAdminUnlockedDep
from admin_service.dependencies.config import AdminConfigDep
from admin_service.dependencies.repositories import AdminRepoDep
from admin_service.dependencies.services import AdminAuthServiceDep


router = APIRouter(prefix="/admins")


@router.get("", response_class=HTMLResponse, name="admin_list")
async def list_admins(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    admin_repo: AdminRepoDep,
) -> Response:
    admins = await admin_repo.list_all()
    return templates.TemplateResponse(
        request,
        "admins/list.html",
        {
            "admin": admin,
            "admins": admins,
            "error": None,
        },
    )


@router.post("/new", name="admin_create")
async def create_admin(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    auth_service: AdminAuthServiceDep,
    admin_repo: AdminRepoDep,
    config: AdminConfigDep,
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
) -> Response:
    username = username.strip()
    if not username or len(username) > 100:
        admins = await admin_repo.list_all()
        return templates.TemplateResponse(
            request,
            "admins/list.html",
            {
                "admin": admin,
                "admins": admins,
                "error": "Недопустимое имя пользователя.",
            },
            status_code=400,
        )
    if len(password) < 8:
        admins = await admin_repo.list_all()
        return templates.TemplateResponse(
            request,
            "admins/list.html",
            {
                "admin": admin,
                "admins": admins,
                "error": "Пароль должен содержать минимум 8 символов.",
            },
            status_code=400,
        )
    existing = await admin_repo.get_by_username(username)
    if existing is not None:
        admins = await admin_repo.list_all()
        return templates.TemplateResponse(
            request,
            "admins/list.html",
            {
                "admin": admin,
                "admins": admins,
                "error": f"Пользователь '{username}' уже существует.",
            },
            status_code=400,
        )
    await auth_service.create_admin(
        acting_admin_id=admin.id,
        username=username,
        password=password,
    )
    return RedirectResponse(
        url=config.url_for("/admins"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{target_id}/disable", name="admin_disable")
async def disable_admin(
    admin: CurrentAdminUnlockedDep,
    auth_service: AdminAuthServiceDep,
    config: AdminConfigDep,
    target_id: Annotated[int, Path(...)],
) -> Response:
    if target_id == admin.id:
        return RedirectResponse(
            url=config.url_for("/admins?error=self_disable"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    await auth_service.set_admin_active(
        acting_admin_id=admin.id,
        target_admin_id=target_id,
        is_active=False,
    )
    return RedirectResponse(
        url=config.url_for("/admins"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{target_id}/enable", name="admin_enable")
async def enable_admin(
    admin: CurrentAdminUnlockedDep,
    auth_service: AdminAuthServiceDep,
    config: AdminConfigDep,
    target_id: Annotated[int, Path(...)],
) -> Response:
    await auth_service.set_admin_active(
        acting_admin_id=admin.id,
        target_admin_id=target_id,
        is_active=True,
    )
    return RedirectResponse(
        url=config.url_for("/admins"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{target_id}/reset-totp", name="admin_reset_totp")
async def reset_totp(
    admin: CurrentAdminUnlockedDep,
    auth_service: AdminAuthServiceDep,
    config: AdminConfigDep,
    target_id: Annotated[int, Path(...)],
) -> Response:
    await auth_service.reset_totp(
        target_admin_id=target_id,
        acting_admin_id=admin.id,
    )
    return RedirectResponse(
        url=config.url_for("/admins"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
