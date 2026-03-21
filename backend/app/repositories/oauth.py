from redis.asyncio import Redis
from app.core.config import Config
from app.dependencies.config import ConfigDep


class OauthRepository:
    _redis: Redis
    _config: Config

    def __init__(self, config: ConfigDep, redis: Redis):
        self._redis = redis
        self._config = config

    async def save_params(self, state: str, nonce: str) -> None:
        await self._redis.setex(f"oauth_state:{state}", self._config.oauth_ttl, nonce)

    async def get_params(self, state: str) -> str | None:
        key = f"oauth_state:{state}"
        nonce = await self._redis.getdel(key)
        return nonce.decode() if nonce else None

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

        user_id_str, sber_id = data.decode().split(":", 1)
        return int(user_id_str), sber_id
