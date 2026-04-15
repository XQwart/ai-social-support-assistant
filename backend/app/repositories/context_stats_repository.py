from __future__ import annotations
from typing import TYPE_CHECKING
import json

from redis.asyncio import Redis

if TYPE_CHECKING:
    from app.core.config import Config


_KEY = "ctx_recent_deltas:"


class ContextStatsRepository:
    _redis: Redis
    _config: Config

    def __init__(self, redis: Redis, config: Config) -> None:
        self._redis = redis
        self._config = config

    async def set_recent_deltas(self, chat_id: int, deltas: list[int]) -> None:
        await self._redis.setex(
            f"{_KEY}{chat_id}",
            self._config.llm_recent_input_deltas_ttl,
            json.dumps(deltas),
        )

    async def get_recent_deltas(self, chat_id: int) -> list[int]:
        raw = await self._redis.get(f"{_KEY}{chat_id}")
        if not raw:
            return []

        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                return []
            return [int(v) for v in data if isinstance(v, (int, float))]
        except Exception:
            return []
