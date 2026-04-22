import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .checkpointer import create_checkpointer
from .config import get_config
from .database import create_engine, create_session_maker
from .redis import create_redis
from .logger import setup_logging
from .http import create_sber_http_client
from .llm import create_llm_clients, create_embedding_client
from .qdrant import create_qdrant_client, ensure_collection


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()

    setup_logging(level=config.log_level)

    engine = create_engine(config)
    session_maker = create_session_maker(engine)
    redis = create_redis(config)
    http_client = create_sber_http_client(config)

    chat_llm_client, compress_llm_client = create_llm_clients(config)
    embedding_client, vector_size = create_embedding_client(config)

    checkpointer = await create_checkpointer(config)
    qdrant = create_qdrant_client(url=config.qdrant_url)
    await ensure_collection(
        qdrant,
        collection_name=config.qdrant_collection,
        vector_size=vector_size,
        distance=config.rag_distance,
    )

    app.state.db_engine = engine
    app.state.session_maker = session_maker
    app.state.checkpointer = checkpointer
    app.state.redis = redis
    app.state.sber_client = http_client

    app.state.chat_llm_client = chat_llm_client
    app.state.compress_llm_client = compress_llm_client
    app.state.embedding_client = embedding_client
    app.state.qdrant = qdrant

    logger.info("Application started successfully")

    try:
        yield
    finally:
        await checkpointer.conn.close()
        await http_client.aclose()
        await qdrant.close()
        await redis.aclose()
        await engine.dispose()
