import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_config
from .database import create_engine, create_session_maker
from .redis import create_redis
from .logger import setup_logging
from .http import create_sber_http_client


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()

    setup_logging(level=config.log_level)

    engine = create_engine(config)
    session_maker = create_session_maker(engine)
    redis = create_redis(config)
    client = create_sber_http_client(config)

    app.state.db_engine = engine
    app.state.session_maker = session_maker
    app.state.redis = redis
    app.state.sber_client = client

    logger.info("Application started successfully")

    try:
        yield
    finally:
        await client.aclose()
        await redis.aclose()
        await engine.dispose()
