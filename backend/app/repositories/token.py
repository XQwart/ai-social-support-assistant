from redis.asyncio import Redis
from app.core.config import Config
from app.dependencies.config import ConfigDep


class TokenRedisRepository:
    _config: Config
    _redis: Redis

    def __init__(self, config: ConfigDep, redis_client: Redis) -> None:
        self._config = config
        self._redis = redis_client

    def _key(self, user_id: int, jti: str) -> str:
        return f"refresh:{user_id}:{jti}"

    async def save(self, user_id: int, jti: str) -> None:
        key = self._key(user_id, jti)
        await self._redis.setex(key, self._config.jwt_refresh_token_expire, jti)

    async def exists(self, user_id: int, jti: str) -> bool:
        key = self._key(user_id, jti)
        return await self._redis.exists(key) > 0

    async def remove_all(self, user_id: int) -> int:
        pattern = f"refresh:{user_id}:*"
        keys = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await self._redis.delete(*keys)
        return 0
