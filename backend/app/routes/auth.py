from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Cookie, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.dependencies.config import ConfigDep
from app.dependencies.services import AuthServiceDep
from app.schemas.auth import AuthExchangeResponse
from app.utils.auth import clear_refresh_cookie, set_refresh_cookie

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


def build_frontend_redirect_url(base_url: str, params: dict[str, str | None]) -> str:
    parsed = urlsplit(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value is not None})

    return urlunsplit(parsed._replace(query=urlencode(query)))


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
    frontend_success_login_url = config.frontend_success_login_url

    if error is not None:
        return RedirectResponse(
            url=build_frontend_redirect_url(
                frontend_success_login_url,
                {
                    "error": error,
                    "description": error_description
                    or "Не удалось завершить вход через Sber ID",
                },
            ),
            status_code=303,
        )

    if code is None or state is None:
        return RedirectResponse(
            url=build_frontend_redirect_url(
                frontend_success_login_url,
                {
                    "error": "invalid_request",
                    "description": "Сбер ID не вернул код авторизации",
                },
            ),
            status_code=303,
        )

    try:
        nonce, saved_frontend_success_login_url = await auth_service.validate_state(
            state
        )
        frontend_success_login_url = (
            saved_frontend_success_login_url or config.frontend_success_login_url
        )

        token_data = await auth_service.exchange_code_for_token(code)
        await auth_service.validate_id_token(
            token_data.id_token, nonce, config.client_id
        )

        login_code = await auth_service.process_user(token_data.access_token)
    except HTTPException as exc:
        return RedirectResponse(
            url=build_frontend_redirect_url(
                frontend_success_login_url,
                {
                    "error": "auth_failed",
                    "description": str(exc.detail),
                },
            ),
            status_code=303,
        )
    except Exception:
        logger.exception("Unexpected Sber ID callback failure")
        return RedirectResponse(
            url=build_frontend_redirect_url(
                frontend_success_login_url,
                {
                    "error": "server_error",
                    "description": "Не удалось завершить вход через Sber ID",
                },
            ),
            status_code=303,
        )

    return RedirectResponse(
        url=build_frontend_redirect_url(
            frontend_success_login_url,
            {"code": login_code},
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


# TODO: Удалить
# @router.post("/login")
# async def login(
#     user_repo: UserRepoDep,
#     token_repo: TokenRedisRepoDep,
#     access_token_util: AccessTokenDep,
#     refresh_token_util: RefreshTokenDep,
# ) -> JSONResponse:  # Затычка
#     bank_id = "wythdgsraferi4538trfhsa7837hfas"
#     name = "Ivan"
#     last_name = "Ivanov"

#     user = await user_repo.get_by_bank_id(bank_id=bank_id)
#     if user is None:
#         user = await user_repo.create(
#             bank_id=bank_id, first_name=name, second_name=last_name
#         )

#     refresh_jti = refresh_token_util.generate_jti()

#     access_token = access_token_util.generate(user_id=user.id)
#     refresh_token = refresh_token_util.generate(
#         user_id=user.id, extra={"jti": refresh_jti}
#     )

#     await token_repo.save(user_id=user.id, jti=refresh_jti)

#     response = JSONResponse(
#         content={"message": "Успешная авторизация", "token": access_token}
#     )
#     set_refresh_cookie(response, refresh_token)

#     return response
