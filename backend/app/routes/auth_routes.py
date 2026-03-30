from __future__ import annotations
import logging

from fastapi import APIRouter, Cookie, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.dependencies.config import ConfigDep
from app.dependencies.services import AuthServiceDep
from app.dependencies.repositories import UserRepoDep, TokenRedisRepoDep
from app.dependencies.jwt import AccessTokenDep, RefreshTokenDep
from app.schemas.auth_schemas import AuthExchangeResponse
from app.utils.cookie_utils import clear_refresh_cookie, set_refresh_cookie
from app.utils import url_utils


router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


@router.get("/sber/params")
async def get_params(
    auth_service: AuthServiceDep,
    config: ConfigDep,
    frontend_url: str | None = Query(default=None),
):
    params = await auth_service.get_and_save_state_and_nonce(
        frontend_success_url=frontend_url
    )

    return JSONResponse(
        {
            "client_id": config.client_id,
            "authorize_url": config.sber_authorize_url,
            "redirect_uri": config.sber_redirect_uri,
            "scopes": config.sber_scopes,
            "name": config.sber_application_name,
            "response_type": "code",
            **params,
        }
    )


@router.get("/sber/callback")
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
        results = await auth_service.process_user(state=state, code=code)
    except HTTPException as exc:
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
        url=url_utils.build_url(redirect_url, {"code": results.login_code}),
        status_code=303,
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
        status_code=303,
    )


@router.get("/exchange")
async def exchange_code(auth_service: AuthServiceDep, token_code: str = Query(...)):
    access_token, refresh_token, user_name = await auth_service.login_user(
        token_code=token_code
    )

    response = JSONResponse(
        content=AuthExchangeResponse(
            message="Успешная авторизация",
            token=access_token,
            user_name=user_name,
        ).model_dump()
    )
    set_refresh_cookie(response, refresh_token)

    return response


@router.post("/refresh")
async def refresh(
    auth_service: AuthServiceDep,
    refresh_token: str | None = Cookie(default=None),
):
    access_token, new_refresh_token = await auth_service.refresh(
        refresh_token=refresh_token
    )

    response = JSONResponse(content={"token": access_token}, status_code=200)
    set_refresh_cookie(response=response, refresh_token=new_refresh_token)

    return response


@router.post("/logout")
async def logout(
    auth_service: AuthServiceDep,
    refresh_token: str | None = Cookie(default=None),
) -> Response:
    await auth_service.logout(refresh_token=refresh_token)

    response = Response(status_code=204)
    clear_refresh_cookie(response)

    return response


@router.post("/mock-login")
async def mock_login(
    user_repo: UserRepoDep,
    token_repo: TokenRedisRepoDep,
    access_token_util: AccessTokenDep,
    refresh_token_util: RefreshTokenDep,
) -> JSONResponse:
    bank_id = "wythdgsraferi4538trfhsa7837hfas"
    name = "Ivan"
    last_name = "Ivanov"

    user = await user_repo.get_by_bank_id(bank_id=bank_id)
    if user is None:
        user = await user_repo.create(
            bank_id=bank_id, first_name=name, second_name=last_name
        )

    refresh_jti = refresh_token_util.generate_jti()

    access_token = access_token_util.generate(user_id=user.id)
    refresh_token = refresh_token_util.generate(
        user_id=user.id, extra={"jti": refresh_jti}
    )

    await token_repo.save(user_id=user.id, jti=refresh_jti)

    response = JSONResponse(
        content={"message": "Успешная авторизация", "token": access_token}
    )
    set_refresh_cookie(response, refresh_token)

    return response
