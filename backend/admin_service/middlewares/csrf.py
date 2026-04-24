from __future__ import annotations
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse, Response

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import ASGIApp

    from admin_service.core.security import CSRFTokenSigner


CSRF_COOKIE_NAME = "admin_csrf"
CSRF_HEADER_NAME = "x-csrf-token"
CSRF_FORM_FIELD = "csrf_token"

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_EXEMPT_PATH_PREFIXES = ("/static/",)
_EXEMPT_PATHS = {"/health"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit CSRF cookie.

    On every request we ensure ``admin_csrf`` cookie is set (issuing a
    signed token if missing). On unsafe methods we require the submitted
    token (header or form field) to equal the cookie value and to be
    properly signed.
    """

    _signer: "CSRFTokenSigner"
    _force_https: bool
    _cookie_path: str

    def __init__(
        self,
        app: "ASGIApp",
        signer: "CSRFTokenSigner",
        force_https: bool = True,
        cookie_path: str = "/",
    ) -> None:
        super().__init__(app)
        self._signer = signer
        self._force_https = force_https
        self._cookie_path = cookie_path or "/"

    async def dispatch(self, request: "Request", call_next) -> Response:
        if self._is_exempt(request.url.path):
            return await call_next(request)

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

        if request.method not in _SAFE_METHODS:
            submitted = await self._extract_submitted_token(request)
            if (
                not cookie_token
                or not submitted
                or submitted != cookie_token
                or not self._signer.validate(cookie_token)
            ):
                return PlainTextResponse(
                    "CSRF validation failed",
                    status_code=403,
                )

        response = await call_next(request)

        if not cookie_token or not self._signer.validate(cookie_token):
            new_token = self._signer.issue()
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=new_token,
                httponly=False,
                secure=self._force_https,
                samesite="strict",
                path=self._cookie_path,
            )

        return response

    def _is_exempt(self, path: str) -> bool:
        if path in _EXEMPT_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in _EXEMPT_PATH_PREFIXES)

    async def _extract_submitted_token(self, request: "Request") -> str | None:
        header = request.headers.get(CSRF_HEADER_NAME)
        if header:
            return header

        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/x-www-form-urlencoded") or \
                content_type.startswith("multipart/form-data"):
            try:
                form = await request.form()
                value = form.get(CSRF_FORM_FIELD)
                if isinstance(value, str):
                    return value
            except Exception:  # noqa: BLE001
                return None
        return None
