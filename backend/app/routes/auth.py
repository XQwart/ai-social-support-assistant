from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.dependencies.services import AuthServiceDep
from app.dependencies.config import ConfigDep

router = APIRouter("/auth")


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
    auth_service: AuthServiceDep, code: str = Query(...), state: str = Query(...)
):
    nonce = await auth_service.validate_state(state)

    token_data = await auth_service.exchange_code_for_token(code)
    await auth_service.validate_nonce(token_data.id_token, nonce)

    code = await auth_service.login_user(token_data.access_token)

    # TODO: Добавить редирект на клиент
