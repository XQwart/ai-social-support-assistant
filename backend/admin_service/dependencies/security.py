from __future__ import annotations
from typing import Annotated

from fastapi import Depends, Request

from admin_service.core.security import AdminSessionToken, CSRFTokenSigner


def get_session_token(request: Request) -> AdminSessionToken:
    return request.app.state.session_token


def get_csrf_signer(request: Request) -> CSRFTokenSigner:
    return request.app.state.csrf_signer


SessionTokenDep = Annotated[AdminSessionToken, Depends(get_session_token)]
CSRFSignerDep = Annotated[CSRFTokenSigner, Depends(get_csrf_signer)]
