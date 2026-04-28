from __future__ import annotations
import contextvars
import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp


request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "admin_request_id", default=None
)
client_ip_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "admin_client_ip", default=None
)
user_agent_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "admin_user_agent", default=None
)
admin_id_ctx: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "admin_admin_id", default=None
)


def _extract_client_ip(request: "Request") -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


class AuditContextMiddleware(BaseHTTPMiddleware):
    """Populates contextvars consumed by :class:`AdminAuditService`."""

    def __init__(self, app: "ASGIApp") -> None:
        super().__init__(app)

    async def dispatch(self, request: "Request", call_next) -> "Response":
        req_token = request_id_ctx.set(uuid.uuid4().hex)
        ip_token = client_ip_ctx.set(_extract_client_ip(request))
        ua_token = user_agent_ctx.set(request.headers.get("user-agent"))
        admin_token = admin_id_ctx.set(None)
        try:
            response = await call_next(request)
            return response
        finally:
            request_id_ctx.reset(req_token)
            client_ip_ctx.reset(ip_token)
            user_agent_ctx.reset(ua_token)
            admin_id_ctx.reset(admin_token)
