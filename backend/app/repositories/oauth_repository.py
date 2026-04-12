import json

from redis.asyncio import Redis
from app.core.config import Config


class OauthRepository:
    _redis: Redis
    _config: Config

    def __init__(self, config: Config, redis: Redis):
        self._redis = redis
        self._config = config

    async def save_params(
        self, state: str, nonce: str, frontend_success_url: str | None = None
    ) -> None:
        payload = json.dumps(
            {
                "nonce": nonce,
                "frontend_success_url": frontend_success_url,
            }
        )
        await self._redis.setex(f"oauth_state:{state}", self._config.oauth_ttl, payload)

    async def get_params(self, state: str) -> tuple[str, str | None] | None:
        key = f"oauth_state:{state}"
        raw_data = await self._redis.getdel(key)
        if not raw_data:
            return None

        try:
            data = json.loads(raw_data)
            return data["nonce"], data.get("frontend_success_url")
        except (json.JSONDecodeError, KeyError, TypeError):
            return raw_data, None

    async def save_code(self, user_id: int, sber_id: str, code: str) -> str:
        await self._redis.setex(
            f"auth_code:{code}", self._config.code_ttl, f"{user_id}:{sber_id}"
        )
        return code

    async def get_code(self, code: str) -> tuple[int, str] | None:
        key = f"auth_code:{code}"
        data = await self._redis.getdel(key)
        if not data:
            return None

        user_id_str, sber_id = data.split(":", 1)
        return int(user_id_str), sber_id
