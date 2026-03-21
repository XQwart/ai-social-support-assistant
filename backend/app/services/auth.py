from __future__ import annotations
from typing import TYPE_CHECKING
import secrets
import uuid

from fastapi import HTTPException
import httpx
import jose.jwt

from app.schemas.auth import SberTokenData, SberUserInfo

if TYPE_CHECKING:
    from app.core.config import Config
    from app.repositories.oauth import OauthRepository
    from app.repositories.user import UserRepository
    from app.repositories.token import TokenRedisRepository


class AuthService:
    _config: Config
    _oauth_rep: OauthRepository
    _token_rep: TokenRedisRepository
    _user_rep: UserRepository

    def __init__(
        self,
        config: Config,
        ouath_rep: OauthRepository,
        token_rep: TokenRedisRepository,
        user_rep: UserRepository,
    ):
        self._config = config
        self._oauth_rep = ouath_rep
        self._token_rep = token_rep
        self._user_rep = user_rep

    async def get_and_save_state_and_nonce(self) -> dict[str, str]:
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        await self._oauth_rep.save_params(state=state, nonce=nonce)

        return {"state": state, "nonce": nonce}

    async def validate_state(self, state: str) -> str:
        nonce = await self._oauth_rep.get_params(state)
        if nonce is None:
            raise HTTPException(400, "Invalid or expired state")

        return nonce

    async def exchange_code_for_token(self, code: str) -> SberTokenData:
        rquid = uuid.uuid4().hex

        async with httpx.AsyncClient(verify=self._config.sber_ca_path) as client:
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
                    "rquid": rquid,
                },
            )

            if token_res.status_code != 200:
                print("❌ Sber Token Error:")
                print(f"Status: {token_res.status_code}")
                print(f"Body: {token_res.text}")
                print(f"Headers: {dict(token_res.headers)}")

                raise HTTPException(
                    status_code=token_res.status_code,
                    detail=f"Sber error: {token_res.text}",
                )

            return SberTokenData(**token_res.json())

    async def validate_id_token(
        self, id_token: str, nonce: str, client_id: str
    ) -> None:
        claims = jose.jwt.get_unverified_claims(id_token)
        if claims.get("nonce") != nonce:
            raise HTTPException(400, "Invalid nonce")
        if claims.get("aud") != client_id:
            raise HTTPException(400, "Invalid aud")

    async def login_user(self, bank_access_token: str) -> str:
        rquid = uuid.uuid4().hex

        async with httpx.AsyncClient(verify=self._config.sber_ca_path) as client:
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

        return code
