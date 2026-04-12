import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .base_exceptions import AppError


logger = logging.getLogger(__name__)


def init_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppError)
    async def app_error_handler(req: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            trace_id = uuid.uuid4().hex
            logger.exception(
                "Server error | traceId=%s | %s %s",
                trace_id,
                req.method,
                req.url,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": "Что-то пошло не так. Попробуйте позже.",
                    "traceId": trace_id,
                },
            )

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(req: Request, _: Exception) -> JSONResponse:
        trace_id = uuid.uuid4().hex
        logger.exception(
            "Unhandled exception | traceId=%s | %s %s",
            trace_id,
            req.method,
            req.url,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Что-то пошло не так. Попробуйте позже.",
                "traceId": trace_id,
            },
        )
