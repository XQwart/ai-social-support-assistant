from datetime import timedelta
from redis.asyncio import Redis


class OauthRepository:
    _redis: Redis

    def __init__(self, redis: Redis):
        self._redis = redis

    async def save_params(self, state: str, nonce: str) -> dict:
        await self._redis.setex(f"oauth_state:{state}", timedelta(minutes=10), nonce)
        return {"state": state, "nonce": nonce}

    async def get_params(self, state: str) -> str | None:
        key = f"oauth_state:{state}"
        nonce = await self._redis.getdel(key)
        return nonce.decode() if nonce else None

    async def save_code(self, user_id: int, sber_id: str, code: str) -> str:
        await self._redis.setex(
            f"auth_code:{code}", timedelta(seconds=30), f"{user_id}:{sber_id}"
        )
        return code

    async def get_code(self, code: str) -> tuple[int, str] | None:
        key = f"auth_code:{code}"
        data = await self._redis.getdel(key)
        if not data:
            return None

        user_id_str, sber_id = data.decode().split(":", 1)
        return int(user_id_str), sber_id
