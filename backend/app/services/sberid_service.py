from __future__ import annotations
import logging
from typing import TYPE_CHECKING

import uuid
import httpx
import jose.jwt

from app.schemas.auth_schemas import SberTokenData, SberUserInfo
from app.exceptions.base_exceptions import BadRequestError, ExternalServiceError

if TYPE_CHECKING:
    from app.core.config import Config


logger = logging.getLogger(__name__)


class SberIdService:
    _config: Config
    _client: httpx.AsyncClient

    def __init__(self, config: Config, client: httpx.AsyncClient) -> None:
        self._config = config
        self._client = client

    async def authenticate(self, code: str, nonce: str) -> SberUserInfo:
        token_data = await self._exchange_code_for_token(code)
        await self._validate_id_token(
            token_data.id_token, nonce, self._config.client_id
        )

        return await self._fetch_userinfo(token_data.access_token)

    async def _exchange_code_for_token(self, code: str) -> SberTokenData:
        rquid = uuid.uuid4().hex

        res = await self._client.post(
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

        if res.status_code != 200:
            logger.error(
                "Sber token exchange failed | rquid=%s | status=%s | body=%s",
                rquid,
                res.status_code,
                res.text,
            )

            raise ExternalServiceError(f"Sber token exchange failed: {res.text}")
        logger.info("Sber token exchange success")

        return SberTokenData(**res.json())

    async def _validate_id_token(
        self, id_token: str, nonce: str, client_id: str
    ) -> None:
        claims = jose.jwt.get_unverified_claims(id_token)
        if claims.get("nonce") != nonce:
            raise BadRequestError("Invalid nonce")
        if claims.get("aud") != client_id:
            raise BadRequestError("Invalid aud")
        logger.debug("id_token validated successfully")

    async def _fetch_userinfo(self, bank_access_token: str) -> SberUserInfo:
        rquid = uuid.uuid4().hex

        res = await self._client.get(
            self._config.sber_userinfo_url,
            headers={
                "Authorization": f"Bearer {bank_access_token}",
                "x-introspect-rquid": rquid,
            },
        )
        return SberUserInfo(**res.json())
