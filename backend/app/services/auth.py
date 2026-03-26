from __future__ import annotations
from typing import TYPE_CHECKING
import ssl
import secrets
import uuid
import logging
from ssl import SSLContext

from fastapi import HTTPException
import httpx
import jose.jwt

from app.schemas.auth import SberTokenData, SberUserInfo

if TYPE_CHECKING:
    from app.core.config import Config
    from app.repositories.oauth import OauthRepository
    from app.repositories.user import UserRepository
    from app.repositories.token import TokenRedisRepository
    from app.utils.jwt import JWTTokenUtil

logger = logging.getLogger(__name__)


class AuthService:
    _config: Config
    _oauth_rep: OauthRepository
    _token_rep: TokenRedisRepository
    _user_rep: UserRepository
    _access_token_util: JWTTokenUtil
    _refresh_token_util: JWTTokenUtil
    _ssl_sber_ctx: SSLContext | None

    def __init__(
        self,
        config: Config,
        ouath_rep: OauthRepository,
        token_rep: TokenRedisRepository,
        user_rep: UserRepository,
        access_token_util: JWTTokenUtil,
        refresh_token_util: JWTTokenUtil,
        ssl_sber_ctx: SSLContext | None = None,
    ):
        self._config = config
        self._oauth_rep = ouath_rep
        self._token_rep = token_rep
        self._user_rep = user_rep
        self._access_token_util = access_token_util
        self._refresh_token_util = refresh_token_util
        self._ssl_sber_ctx = ssl_sber_ctx

    def _get_ssl_sber_ctx(self) -> SSLContext:
        if self._ssl_sber_ctx is not None:
            return self._ssl_sber_ctx

        try:
            ssl_ctx = ssl.create_default_context(cafile=self._config.sber_ca_cert_path)
            ssl_ctx.load_cert_chain(
                certfile=self._config.sber_client_cert_path,
                keyfile=self._config.sber_client_key_path,
            )
        except FileNotFoundError as exc:
            logger.exception("Sber certificates not found")
            raise HTTPException(500, "Sber certificates are not configured") from exc
        except ssl.SSLError as exc:
            logger.exception("Sber certificates are invalid")
            raise HTTPException(500, "Sber certificates are invalid") from exc

        self._ssl_sber_ctx = ssl_ctx
        return ssl_ctx

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

    async def validate_state(self, state: str) -> tuple[str, str | None]:
        params = await self._oauth_rep.get_params(state)
        if params is None:
            raise HTTPException(400, "Invalid or expired state")

        return params

    async def exchange_code_for_token(self, code: str) -> SberTokenData:
        rquid = uuid.uuid4().hex

        async with httpx.AsyncClient(verify=self._get_ssl_sber_ctx()) as client:
            token_res = await client.post(
                self._config.sber_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self._config.sber_redirect_uri,
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "RqUID": rquid,
                },
            )

            if token_res.status_code != 200:
                logger.error(
                    "Sber token exchange failed | rquid=%s | status=%s | body=%s",
                    rquid,
                    token_res.status_code,
                    token_res.text,
                )

                raise HTTPException(
                    status_code=token_res.status_code,
                    detail=f"Sber error: {token_res.text}",
                )
            logger.info("Sber token exchange success")

            return SberTokenData(**token_res.json())

    async def validate_id_token(
        self, id_token: str, nonce: str, client_id: str
    ) -> None:
        claims = jose.jwt.get_unverified_claims(id_token)
        if claims.get("nonce") != nonce:
            raise HTTPException(400, "Invalid nonce")
        if claims.get("aud") != client_id:
            raise HTTPException(400, "Invalid aud")
        logger.debug("id_token validated successfully")

    async def process_user(self, bank_access_token: str) -> str:
        rquid = uuid.uuid4().hex

        async with httpx.AsyncClient(verify=self._get_ssl_sber_ctx()) as client:
            userinfo_res = await client.get(
                self._config.sber_userinfo_url,
                headers={
                    "Authorization": f"Bearer {bank_access_token}",
                    "x-introspect-rquid": rquid,
                },
            )
            user_data = SberUserInfo(**userinfo_res.json())

        user = await self._user_rep.get_by_bank_id(user_data.sub)

        if user is None:
            user = await self._user_rep.create(
                bank_id=user_data.sub,
                first_name=user_data.given_name,
                second_name=user_data.family_name,
            )

        code = secrets.token_urlsafe(32)
        await self._oauth_rep.save_code(user.id, user.bank_id, code)
        logger.debug("Auth code saved for user")

        return code

    async def login_user(self, token_code: str) -> tuple[str, str, str]:
        code_data = await self._oauth_rep.get_code(code=token_code)
        if code_data is None:
            raise HTTPException(400, "Invalid code")

        user_id, _ = code_data
        user = await self._user_rep.get_by_id(user_id)
        if user is None:
            raise HTTPException(404, "User not found")

        access, refresh = await self._generate_and_save_tokens(user_id=user_id)
        user_name = (
            " ".join(
                part for part in [user.second_name, user.first_name] if part
            ).strip()
            or "Пользователь"
        )

        return access, refresh, user_name

    async def refresh(self, refresh_token: str | None) -> tuple[str, str]:
        if refresh_token is None:
            raise HTTPException(401, "Unauthorized")

        payload = self._refresh_token_util.validate(refresh_token)
        if payload is None:
            raise HTTPException(401, "Unauthorized")

        user_id = payload["sub"]
        refresh_jti = payload["jti"]
        is_removed = await self._token_rep.remove(user_id=user_id, jti=refresh_jti)
        if not is_removed:
            raise HTTPException(401, "Unauthorized")

        access, refresh = await self._generate_and_save_tokens(user_id=user_id)

        return access, refresh

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token is None:
            return

        payload = self._refresh_token_util.validate(refresh_token)
        if payload is None:
            return

        user_id = payload["sub"]
        refresh_jti = payload["jti"]

        await self._token_rep.remove(user_id=user_id, jti=refresh_jti)

    async def _generate_and_save_tokens(self, user_id: int) -> tuple[str, str]:
        refresh_jti = self._refresh_token_util.generate_jti()

        access_token = self._access_token_util.generate(user_id=user_id)
        refresh_token = self._refresh_token_util.generate(
            user_id=user_id, extra={"jti": refresh_jti}
        )

        await self._token_rep.save(user_id=user_id, jti=refresh_jti)

        return access_token, refresh_token
