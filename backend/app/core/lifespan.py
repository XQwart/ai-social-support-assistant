from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import get_config
from .database import create_engine, create_session_maker
from .redis import create_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()

    engine = create_engine(config)
    session_maker = create_session_maker(engine)

    redis = create_redis(config)

    app.state.db_engine = engine
    app.state.session_maker = session_maker

    app.state.redis = redis

    yield

    await redis.aclose()
    await engine.dispose()
