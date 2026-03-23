from __future__ import annotations

from fastapi import APIRouter, Query, Cookie, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.dependencies.auth import AuthDep
from app.dependencies.services import AuthServiceDep
from app.dependencies.config import ConfigDep

from app.utils.auth import set_refresh_cookie, clear_refresh_cookie

# Временно
from app.dependencies.repositories import UserRepoDep, TokenRedisRepoDep
from app.dependencies.jwt import AccessTokenDep, RefreshTokenDep

router = APIRouter(prefix="/auth")


@router.get("/sber/params")
async def get_params(auth_service: AuthServiceDep, config: ConfigDep):
    params = await auth_service.get_and_save_state_and_nonce()

    return JSONResponse(
        {
            "client_id": config.client_id,
            "redirect_uri": config.sber_redirect_uri,
            "scopes": "openid name",
            "response_type": "code",
            **params,
        }
    )


@router.get("/sber/callback")
async def sber_callback(
    auth_service: AuthServiceDep,
    config: ConfigDep,
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    nonce = await auth_service.validate_state(state)

    token_data = await auth_service.exchange_code_for_token(code)
    await auth_service.validate_id_token(token_data.id_token, nonce, config.client_id)

    code = await auth_service.login(token_data.access_token)

    return RedirectResponse(url=f"{config.frontend_success_login_url}?code={code}")


@router.post("/refresh")
async def refresh(
    token_data: AuthDep,
    auth_service: AuthServiceDep,
    refresh_token: str | None = Cookie(default=None),
):
    access_token, new_refresh_token = await auth_service.refresh(
        refresh_token=refresh_token
    )

    response = JSONResponse(content={"token": access_token}, status_code=)
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


@router.post("/login")
async def login(
    user_repo: UserRepoDep,
    token_repo: TokenRedisRepoDep,
    access_token_util: AccessTokenDep,
    refresh_token_util: RefreshTokenDep,
) -> JSONResponse:  # Затычка
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
