from __future__ import annotations
from typing import TYPE_CHECKING

from redis.asyncio import Redis

if TYPE_CHECKING:
    from app.core.config import Config


def create_redis(config: Config) -> Redis:
    return Redis.from_url(
        config.redis_url,
        decode_responses=True,
    )
