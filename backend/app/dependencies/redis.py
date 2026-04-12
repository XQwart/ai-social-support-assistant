from typing import Annotated

from fastapi import Request, Depends
from redis.asyncio import Redis


def get_redis(req: Request) -> Redis:
    return req.app.state.redis


RedisDep = Annotated[Redis, Depends(get_redis)]
