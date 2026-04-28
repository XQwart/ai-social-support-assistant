from __future__ import annotations
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from admin_service.core.config import get_admin_config
from admin_service.core.security import (
    render_totp_qr_data_uri,
    totp_provisioning_uri,
)
from admin_service.core.templating import templates
from admin_service.dependencies.auth import (
    SESSION_COOKIE_NAME,
    CurrentAdminDep,
)
from admin_service.dependencies.config import AdminConfigDep
from admin_service.dependencies.services import (
    AdminAuthServiceDep,
)
from admin_service.middlewares.audit_context import client_ip_ctx
from admin_service.services.admin_auth_service import LoginFailure


logger = logging.getLogger(__name__)


router = APIRouter()


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------
@router.get("/login", response_class=HTMLResponse, name="login_form")
async def login_form(request: Request) -> Response:
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"error": None, "username": ""},
    )


@router.post("/login", name="login_submit")
async def login_submit(
    request: Request,
    auth_service: AdminAuthServiceDep,
    config: AdminConfigDep,
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    totp: Annotated[str | None, Form()] = None,
) -> Response:
    result = await auth_service.login(
        username=username,
        password=password,
        totp_code=totp or None,
        client_ip=client_ip_ctx.get(),
    )

    if result.failure == LoginFailure.TOTP_REQUIRED:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Введите код подтверждения 2FA.",
                "username": username,
                "totp_required": True,
            },
            status_code=200,
        )

    if result.failure == LoginFailure.TOTP_INVALID:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Неверный код 2FA.",
                "username": username,
                "totp_required": True,
            },
            status_code=200,
        )

    if result.failure == LoginFailure.RATE_LIMITED:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": ("Слишком много попыток. Попробуйте позже."),
                "username": username,
            },
            status_code=429,
        )

    if not result.ok:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Неверный логин или пароль.",
                "username": username,
            },
            status_code=200,
        )

    response = RedirectResponse(
        url=config.url_for("/"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result.token,
        httponly=True,
        secure=config.admin_force_https,
        samesite="strict",
        max_age=int(config.session_ttl.total_seconds()),
        path=config.cookie_path,
    )

    if result.admin and result.admin.must_change_password:
        response.headers["Location"] = config.url_for("/change-password")

    return response


@router.post("/logout", name="logout")
async def logout(
    auth_service: AdminAuthServiceDep,
    admin: CurrentAdminDep,
    config: AdminConfigDep,
) -> Response:
    await auth_service.logout(admin.id)
    response = RedirectResponse(
        url=config.url_for("/login"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie(SESSION_COOKIE_NAME, path=config.cookie_path)
    return response


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------
@router.get(
    "/change-password", response_class=HTMLResponse, name="change_password_form"
)
async def change_password_form(
    request: Request,
    admin: CurrentAdminDep,
) -> Response:
    return templates.TemplateResponse(
        request,
        "auth/change_password.html",
        {
            "admin": admin,
            "error": None,
            "must_change": admin.must_change_password,
        },
    )


@router.post("/change-password", name="change_password_submit")
async def change_password_submit(
    request: Request,
    auth_service: AdminAuthServiceDep,
    admin: CurrentAdminDep,
    config: AdminConfigDep,
    current_password: Annotated[str, Form(...)],
    new_password: Annotated[str, Form(...)],
    confirm_password: Annotated[str, Form(...)],
) -> Response:
    if new_password != confirm_password:
        return templates.TemplateResponse(
            request,
            "auth/change_password.html",
            {
                "admin": admin,
                "error": "Пароли не совпадают.",
                "must_change": admin.must_change_password,
            },
            status_code=400,
        )
    if len(new_password) < 8:
        return templates.TemplateResponse(
            request,
            "auth/change_password.html",
            {
                "admin": admin,
                "error": "Пароль должен содержать минимум 8 символов.",
                "must_change": admin.must_change_password,
            },
            status_code=400,
        )

    ok = await auth_service.change_password(
        admin_id=admin.id,
        current_password=current_password,
        new_password=new_password,
    )
    if not ok:
        return templates.TemplateResponse(
            request,
            "auth/change_password.html",
            {
                "admin": admin,
                "error": "Неверный текущий пароль.",
                "must_change": admin.must_change_password,
            },
            status_code=400,
        )

    return RedirectResponse(
        url=config.url_for("/"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ---------------------------------------------------------------------------
# TOTP
# ---------------------------------------------------------------------------
@router.get("/totp/enroll", response_class=HTMLResponse, name="totp_enroll")
async def totp_enroll(
    request: Request,
    auth_service: AdminAuthServiceDep,
    admin: CurrentAdminDep,
) -> Response:
    config = get_admin_config()
    result = await auth_service.begin_totp_enrollment(admin.id)
    if result is None:
        return RedirectResponse(url=config.url_for("/"), status_code=303)
    secret, _uri = result
    uri = totp_provisioning_uri(secret, admin.username, config.admin_totp_issuer)
    qr_data_uri = render_totp_qr_data_uri(uri)
    return templates.TemplateResponse(
        request,
        "auth/totp_enroll.html",
        {
            "admin": admin,
            "secret": secret,
            "qr_data_uri": qr_data_uri,
            "error": None,
        },
    )


@router.post("/totp/verify", name="totp_verify")
async def totp_verify(
    request: Request,
    auth_service: AdminAuthServiceDep,
    admin: CurrentAdminDep,
    config: AdminConfigDep,
    code: Annotated[str, Form(...)],
) -> Response:
    ok = await auth_service.confirm_totp_enrollment(admin.id, code)
    if not ok:
        return templates.TemplateResponse(
            request,
            "auth/totp_enroll.html",
            {
                "admin": admin,
                "secret": admin.totp_secret,
                "qr_data_uri": None,
                "error": "Неверный код. Попробуйте ещё раз.",
            },
            status_code=400,
        )
    return RedirectResponse(url=config.url_for("/"), status_code=303)
