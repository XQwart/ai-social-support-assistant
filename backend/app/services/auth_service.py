from __future__ import annotations
from typing import TYPE_CHECKING
import secrets
import logging

from app.schemas.auth_schemas import (
    SberUserInfo,
    SberCallbackResult,
    AuthTokenPair,
    LoginResult,
)
from app.exceptions.base_exceptions import (
    BadRequestError,
    NotAuthenticatedError,
    NotFoundError,
)

if TYPE_CHECKING:
    from . import SberIdService
    from app.core.config import Config
    from app.models import UserModel
    from app.repositories import TokenRedisRepository, OauthRepository, UserRepository
    from app.utils.jwt_utils import JWTTokenUtil


logger = logging.getLogger(__name__)


class AuthService:
    _config: Config
    _sberid_service: SberIdService
    _oauth_rep: OauthRepository
    _token_rep: TokenRedisRepository
    _user_rep: UserRepository
    _access_token_util: JWTTokenUtil
    _refresh_token_util: JWTTokenUtil

    def __init__(
        self,
        config: Config,
        sberid_service: SberIdService,
        ouath_rep: OauthRepository,
        token_rep: TokenRedisRepository,
        user_rep: UserRepository,
        access_token_util: JWTTokenUtil,
        refresh_token_util: JWTTokenUtil,
    ):
        self._config = config
        self._sberid_service = sberid_service
        self._oauth_rep = ouath_rep
        self._token_rep = token_rep
        self._user_rep = user_rep
        self._access_token_util = access_token_util
        self._refresh_token_util = refresh_token_util

    async def get_and_save_state_and_nonce(
        self, frontend_success_url: str | None = None
    ) -> dict[str, str]:
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        await self._oauth_rep.save_params(
            state=state,
            nonce=nonce,
            frontend_success_url=frontend_success_url,
        )

        return {"state": state, "nonce": nonce}

    async def handle_sber_callback(self, state: str, code: str) -> SberCallbackResult:
        nonce, saved_redirect_url = await self._validate_state(state)

        user_info = await self._sberid_service.authenticate(code=code, nonce=nonce)
        user = await self._get_or_create_user(user_info)

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

    async def _get_or_create_user(self, user_info: SberUserInfo) -> UserModel:
        user = await self._user_rep.get_by_bank_id(user_info.sub)

        if user is None:
            user = await self._user_rep.create(
                bank_id=user_info.sub,
                first_name=user_info.given_name,
                second_name=user_info.family_name,
            )

        return user

    async def login_user(self, token_code: str) -> LoginResult:
        code_data = await self._oauth_rep.get_code(code=token_code)
        if code_data is None:
            raise BadRequestError("Invalid code")

        user_id, _ = code_data
        user = await self._user_rep.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        tokens = await self._generate_and_save_tokens(user_id=user_id)
        user_name = (
            " ".join(
                part for part in [user.second_name, user.first_name] if part
            ).strip()
            or "Пользователь"
        )

        return LoginResult(user_name=user_name, tokens=tokens)

    async def refresh(self, refresh_token: str | None) -> AuthTokenPair:
        if refresh_token is None:
            raise NotAuthenticatedError("Refresh token missing")

        payload = self._refresh_token_util.validate(refresh_token)
        if payload is None:
            raise NotAuthenticatedError("Invalid refresh token")

        user_id = payload["sub"]
        refresh_jti = payload["jti"]
        is_removed = await self._token_rep.remove(user_id=user_id, jti=refresh_jti)
        if not is_removed:
            raise NotAuthenticatedError("Refresh token revoked")

        return await self._generate_and_save_tokens(user_id=user_id)

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
