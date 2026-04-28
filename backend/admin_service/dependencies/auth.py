from __future__ import annotations
from typing import Annotated, TYPE_CHECKING

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from admin_service.core.config import get_admin_config
from admin_service.dependencies.repositories import AdminRepoDep
from admin_service.dependencies.security import SessionTokenDep
from admin_service.middlewares.audit_context import admin_id_ctx

if TYPE_CHECKING:
    from shared.models import Admin


SESSION_COOKIE_NAME = "admin_session"


class _AdminRedirect(HTTPException):
    """Special exception caught in main app to redirect to /login.

    ``location`` is an internal path (e.g. ``"/login"``); the admin
    base path is prepended automatically so the browser stays inside
    the admin namespace when running behind nginx.
    """

    def __init__(self, location: str = "/login") -> None:
        config = get_admin_config()
        absolute = config.url_for(location)
        super().__init__(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": absolute},
            detail="Authentication required",
        )


async def get_current_admin(
    admin_repo: AdminRepoDep,
    token_util: SessionTokenDep,
    admin_session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> "Admin":
    if not admin_session:
        raise _AdminRedirect()

    payload = token_util.decode(admin_session)
    if not payload:
        raise _AdminRedirect()

    try:
        admin_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        raise _AdminRedirect()

    if admin_id <= 0:
        raise _AdminRedirect()

    admin = await admin_repo.get_by_id(admin_id)
    if admin is None or not admin.is_active:
        raise _AdminRedirect()

    admin_id_ctx.set(admin.id)
    return admin


CurrentAdminDep = Annotated["Admin", Depends(get_current_admin)]


async def get_current_admin_unlocked(admin: CurrentAdminDep) -> "Admin":
    """Like :func:`get_current_admin` but redirects to change-password if forced."""
    if admin.must_change_password:
        raise _AdminRedirect("/change-password")
    return admin


CurrentAdminUnlockedDep = Annotated[
    "Admin", Depends(get_current_admin_unlocked)
]
