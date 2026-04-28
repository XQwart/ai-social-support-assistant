from __future__ import annotations
from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from admin_service.core.templating import templates
from admin_service.dependencies.auth import CurrentAdminUnlockedDep
from admin_service.dependencies.repositories import AdminAuditRepoDep

if TYPE_CHECKING:
    pass


router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="dashboard")
async def dashboard(
    request: Request,
    admin: CurrentAdminUnlockedDep,
    audit_repo: AdminAuditRepoDep,
) -> Response:
    recent = await audit_repo.recent(limit=50)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "admin": admin,
            "audit_entries": recent,
        },
    )


@router.get("/health", name="health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
