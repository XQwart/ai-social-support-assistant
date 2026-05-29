from __future__ import annotations
import logging
import uuid
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from admin_service.core.config import get_admin_config
from admin_service.core.templating import templates
from admin_service.dependencies.auth import _AdminRedirect

if TYPE_CHECKING:
    from fastapi import FastAPI


logger = logging.getLogger(__name__)


def init_exception_handlers(app: "FastAPI") -> None:
    @app.exception_handler(_AdminRedirect)
    async def admin_redirect_handler(
        _request: Request, exc: _AdminRedirect
    ) -> RedirectResponse:
        config = get_admin_config()
        fallback = config.url_for("/login")
        location = exc.headers.get("Location", fallback) if exc.headers else fallback
        return RedirectResponse(url=location, status_code=303)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> HTMLResponse:
        if exc.status_code == 404:
            return templates.TemplateResponse(
                request,
                "error.html",
                {
                    "title": "Не найдено",
                    "message": "Запрашиваемая страница не найдена.",
                    "status_code": 404,
                },
                status_code=404,
            )
        if exc.status_code == 403:
            return templates.TemplateResponse(
                request,
                "error.html",
                {
                    "title": "Доступ запрещён",
                    "message": str(exc.detail) if exc.detail else "Доступ запрещён.",
                    "status_code": 403,
                },
                status_code=403,
            )
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": "Ошибка",
                "message": str(exc.detail) if exc.detail else "Произошла ошибка.",
                "status_code": exc.status_code,
            },
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> HTMLResponse:
        if isinstance(exc, HTTPException):
            raise exc
        trace_id = uuid.uuid4().hex
        logger.exception(
            "Admin: unhandled exception | traceId=%s | %s %s",
            trace_id,
            request.method,
            request.url,
        )
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "title": "Внутренняя ошибка",
                "message": (
                    "Произошла непредвиденная ошибка. Сообщите администратору "
                    f"трейс {trace_id}."
                ),
                "status_code": 500,
            },
            status_code=500,
        )
