from __future__ import annotations
import logging

from fastapi import APIRouter, Cookie, Query, status
from fastapi.responses import RedirectResponse, Response

from app.dependencies.config import ConfigDep
from app.dependencies.services import AuthServiceDep
from app.exceptions.base_exceptions import AppError
from app.schemas.auth_schemas import (
    AuthExchangeResponse,
    SberParamsResponse,
    RefreshResponse,
)
from app.schemas.user_schemas import UserOut
from app.utils.cookie_utils import clear_refresh_cookie, set_refresh_cookie
from app.utils import url_utils


router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


@router.get("/sber/params", status_code=status.HTTP_200_OK)
async def get_params(
    auth_service: AuthServiceDep,
    config: ConfigDep,
    frontend_url: str | None = Query(default=None),
) -> SberParamsResponse:
    state, nonce = await auth_service.get_and_save_state_and_nonce(
        frontend_success_url=frontend_url
    )

    return SberParamsResponse(
        client_id=config.client_id,
        authorize_url=config.sber_authorize_url,
        redirect_uri=config.sber_redirect_uri,
        scopes=config.sber_scopes,
        name=config.sber_application_name,
        response_type="code",
        state=state,
        nonce=nonce,
    )


@router.get("/sber/callback", status_code=status.HTTP_303_SEE_OTHER)
async def sber_callback(
    auth_service: AuthServiceDep,
    config: ConfigDep,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> RedirectResponse:
    default_redirect = config.frontend_url

    if error is not None:
        return _error_redirect(
            url=default_redirect,
            error=error,
            description=error_description or "Не удалось завершить вход через Sber ID",
        )

    if code is None or state is None:
        return _error_redirect(
            url=default_redirect,
            error="invalid_request",
            description="Sber ID не вернул код авторизации",
        )

    try:
        results = await auth_service.handle_sber_callback(state=state, code=code)
    except AppError as exc:
        return _error_redirect(
            url=default_redirect, error="auth_failed", description=str(exc.detail)
        )
    except Exception:
        logger.exception("Unexpected Sber ID callback failure")
        return _error_redirect(
            url=default_redirect,
            error="server_error",
            description="Не удалось завершить вход через Sber ID",
        )

    redirect_url = results.redirect_url or default_redirect

    return RedirectResponse(
        url=url_utils.build_url(redirect_url, {"code": results.login_code})
    )


def _error_redirect(url: str, error: str, description: str) -> RedirectResponse:
    return RedirectResponse(
        url=url_utils.build_url(
            base_url=url,
            params={
                "error": error,
                "description": description,
            },
        ),
    )


@router.get("/exchange", status_code=status.HTTP_200_OK)
async def exchange_code(
    auth_service: AuthServiceDep, response: Response, token_code: str = Query(...)
) -> AuthExchangeResponse:
    user, tokens = await auth_service.login_user(token_code=token_code)

    set_refresh_cookie(response, tokens.refresh_token)

    return AuthExchangeResponse(
        message="Успешная авторизация",
        user=UserOut.model_validate(user),
        token=tokens.access_token,
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    auth_service: AuthServiceDep,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
) -> RefreshResponse:
    tokens = await auth_service.refresh(refresh_token=refresh_token)

    set_refresh_cookie(response, tokens.refresh_token)

    return RefreshResponse(token=tokens.access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    auth_service: AuthServiceDep,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
) -> None:
    await auth_service.logout(refresh_token=refresh_token)

    clear_refresh_cookie(response)


@router.post("/mock-login")
async def mock_login(
    auth_service: AuthServiceDep, response: Response
) -> AuthExchangeResponse:
    user, tokens = await auth_service.mock_login_user()

    set_refresh_cookie(response, tokens.refresh_token)

    return AuthExchangeResponse(
        message="Успешная авторизация",
        user=UserOut.model_validate(user),
        token=tokens.access_token,
    )
