from __future__ import annotations
from typing import TYPE_CHECKING
import secrets
import logging

from app.schemas.auth_schemas import (
    SberCallbackResult,
    AuthTokenPair,
)
from app.exceptions.base_exceptions import BadRequestError, NotAuthenticatedError

if TYPE_CHECKING:
    from . import SberIdService, UserService
    from app.core.config import Config
    from app.models import UserModel
    from app.repositories import TokenRedisRepository, OauthRepository
    from app.utils.jwt_utils import JWTTokenUtil


logger = logging.getLogger(__name__)


class AuthService:
    _config: Config
    _sberid_service: SberIdService
    _oauth_rep: OauthRepository
    _token_rep: TokenRedisRepository
    _user_service: UserService
    _access_token_util: JWTTokenUtil
    _refresh_token_util: JWTTokenUtil

    def __init__(
        self,
        config: Config,
        sberid_service: SberIdService,
        ouath_rep: OauthRepository,
        token_rep: TokenRedisRepository,
        user_service: UserService,
        access_token_util: JWTTokenUtil,
        refresh_token_util: JWTTokenUtil,
    ):
        self._config = config
        self._sberid_service = sberid_service
        self._oauth_rep = ouath_rep
        self._token_rep = token_rep
        self._user_service = user_service
        self._access_token_util = access_token_util
        self._refresh_token_util = refresh_token_util

    async def get_and_save_state_and_nonce(
        self, frontend_success_url: str | None = None
    ) -> tuple[str, str]:
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        await self._oauth_rep.save_params(
            state=state,
            nonce=nonce,
            frontend_success_url=frontend_success_url,
        )

        return state, nonce

    async def handle_sber_callback(self, state: str, code: str) -> SberCallbackResult:
        nonce, saved_redirect_url = await self._validate_state(state)

        user_info = await self._sberid_service.authenticate(code=code, nonce=nonce)
        user = await self._user_service.get_or_create_by_bank_id(
            bank_id=user_info.sub,
            first_name=user_info.given_name,
            second_name=user_info.family_name,
            place_of_work=user_info.place_of_work,
        )

        login_code = secrets.token_urlsafe(32)
        await self._oauth_rep.save_code(user.id, user.bank_id, code)

        return SberCallbackResult(
            login_code=login_code, redirect_url=saved_redirect_url
        )

    async def _validate_state(self, state: str) -> tuple[str, str | None]:
        params = await self._oauth_rep.get_params(state)
        if params is None:
            raise BadRequestError("Invalid or expired state")

        return params

    async def mock_login_user(self) -> tuple[UserModel, AuthTokenPair]:
        bank_id = "wythdgsraferi4538trfhsa7837hfas"
        name = "Ivan"
        last_name = "Ivanov"
        place_of_work = "Sberbank"

        user = await self._user_service.get_or_create_by_bank_id(
            bank_id=bank_id,
            first_name=name,
            second_name=last_name,
            place_of_work=place_of_work,
        )

        tokens = await self._generate_and_save_tokens(user_id=user.id)

        return user, tokens

    async def login_user(self, token_code: str) -> tuple[UserModel, AuthTokenPair]:
        code_data = await self._oauth_rep.get_code(code=token_code)
        if code_data is None:
            raise BadRequestError("Invalid code")

        user_id, _ = code_data
        user = await self._user_service.get_by_id(user_id)

        tokens = await self._generate_and_save_tokens(user_id=user_id)

        return user, tokens

    async def refresh(
        self, refresh_token: str | None
    ) -> tuple[UserModel, AuthTokenPair]:
        if refresh_token is None:
            raise NotAuthenticatedError("Refresh token missing")

        payload = self._refresh_token_util.validate(refresh_token)
        if payload is None:
            raise NotAuthenticatedError("Invalid refresh token")

        user_id = int(payload["sub"])
        refresh_jti = payload["jti"]
        is_removed = await self._token_rep.remove(user_id=user_id, jti=refresh_jti)
        if not is_removed:
            raise NotAuthenticatedError("Refresh token revoked")

        # TODO: Сделать обновление данных и их перезапись в бд
        user = await self._user_service.get_by_id(
            user_id=user_id
        )  # Пока просто возврат старого пользователя
        tokens = await self._generate_and_save_tokens(user_id=user_id)

        return user, tokens

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token is None:
            return

        payload = self._refresh_token_util.validate(refresh_token)
        if payload is None:
            return

        user_id = payload["sub"]
        refresh_jti = payload["jti"]

        await self._token_rep.remove(user_id=user_id, jti=refresh_jti)

    async def _generate_and_save_tokens(self, user_id: int) -> AuthTokenPair:
        refresh_jti = self._refresh_token_util.generate_jti()

        access_token = self._access_token_util.generate(user_id=user_id)
        refresh_token = self._refresh_token_util.generate(
            user_id=user_id, extra={"jti": refresh_jti}
        )

        await self._token_rep.save(user_id=user_id, jti=refresh_jti)

        return AuthTokenPair(access_token=access_token, refresh_token=refresh_token)
