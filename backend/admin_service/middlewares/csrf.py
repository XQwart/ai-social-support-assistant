from __future__ import annotations
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse, Response
from starlette.requests import Request

if TYPE_CHECKING:
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
            body = await request.body()

            submitted = self._extract_submitted_token_raw(
                body=body,
                headers=request.headers,
            )

            request = Request(request.scope, receive=self._make_receive(body))

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

        need_new_cookie = False

        if cookie_token and self._signer.validate(cookie_token):
            request.state.csrf_token = cookie_token
        else:
            request.state.csrf_token = self._signer.issue()
            need_new_cookie = True

        response = await call_next(request)

        if need_new_cookie:
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=request.state.csrf_token,
                httponly=False,
                secure=self._force_https,
                samesite="strict",
                path=self._cookie_path,
            )

        return response

    def _make_receive(self, body: bytes):
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        return receive

    def _is_exempt(self, path: str) -> bool:
        if path in _EXEMPT_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in _EXEMPT_PATH_PREFIXES)

    def _extract_submitted_token_raw(self, headers, body: bytes) -> str | None:
        header = headers.get(CSRF_HEADER_NAME)
        if header:
            return header

        content_type = headers.get("content-type", "")
        if content_type.startswith("application/x-www-form-urlencoded"):
            data = parse_qs(body.decode("utf-8", "ignore"))
            v = data.get(CSRF_FORM_FIELD, [None])[0]
            return v if isinstance(v, str) else None

        return None
