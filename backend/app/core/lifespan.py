import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_config
from .database import create_engine, create_session_maker
from .redis import create_redis
from .logger import setup_logging
from .http import create_sber_http_client
from .ai import create_ai_clients


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()

    setup_logging(level=config.log_level)

    engine = create_engine(config)
    session_maker = create_session_maker(engine)
    redis = create_redis(config)
    http_client = create_sber_http_client(config)
    chat_ai_client, compress_ai_client, embedding_ai_client = create_ai_clients(config)

    app.state.db_engine = engine
    app.state.session_maker = session_maker
    app.state.redis = redis
    app.state.sber_client = http_client

    app.state.chat_ai_client = chat_ai_client
    app.state.compress_ai_client = compress_ai_client
    app.state.embedding_ai_client = embedding_ai_client

    logger.info("Application started successfully")

    try:
        yield
    finally:
        await chat_ai_client.aclose()
        await compress_ai_client.aclose()
        await embedding_ai_client.aclose()

        await http_client.aclose()
        await redis.aclose()
        await engine.dispose()
