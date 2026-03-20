from __future__ import annotations
from typing import TYPE_CHECKING
import secrets

from fastapi import HTTPException
import httpx
import jose.jwt

from app.dependencies.config import ConfigDep
from app.schemas.auth import SberTokenData, SberUserInfo

if TYPE_CHECKING:
    from app.core.config import Config


class AuthService:
    _config: Config

    def __init__(self, config: ConfigDep):  # TODO: Принимать репозиторий с oauth и auth
        self._config = config

    async def get_and_save_oauth_params(self) -> dict[str, str]:
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        # TODO: Добавить сохранение в редис

        return {"state": state, "nonce": nonce}

    async def validate_oauth_params(self, code: str, state: str) -> None:
        pass

    async def exchange_code_for_token(self, code: str) -> SberTokenData:
        async with httpx.AsyncClient() as client:
            token_res = await client.post(
                self._config.redirect_uri,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self._config.redirect_uri,
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                },
            )

            if token_res.status_code != 200:
                raise HTTPException(400, detail="Token exchange failed")

            return SberTokenData(**token_res.json())

    async def validate_nonce(self, id_token: str, nonce: str) -> None:
        claims = jose.jwt.get_unverified_claims(id_token)
        if claims.get("nonce") != nonce:
            raise HTTPException(400, "Invalid nonce")

    async def login_user(self, sber_access_token: str) -> str:
        async with httpx.AsyncClient() as client:
            userinfo_res = await client.get(
                self._config.userinfo_url,
                headers={"Authorization": f"Bearer {sber_access_token}"},
            )
            user_data = SberUserInfo(**userinfo_res.json())

        # TODO: Сохранение пользователя в бд

        code = secrets.token_urlsafe(32)
        # TODO: Сохранить код

        return code
