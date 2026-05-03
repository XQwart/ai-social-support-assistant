from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from worker.core.config import get_config
from worker.core.database import create_engine, create_session_maker
from worker.core.embeding import build_embedding_provider
from worker.core.llm import build_llm_client
from worker.core.qdrant import create_qdrant_client, ensure_collections
from worker.core.logger import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()

    setup_logging(level=config.log_level)

    engine = create_engine(config)
    session_maker = create_session_maker(engine)

    embedding_provider = build_embedding_provider(config)

    llm_client = build_llm_client(config)

    qdrant = create_qdrant_client(url=config.qdrant_url)
    await ensure_collections(
        client=qdrant,
        collection_name=config.chunks_collection_name,
        vector_size=embedding_provider.vector_size,
    )

    app.state.config = config
    app.state.db_engine = engine
    app.state.embedding_model = embedding_provider.model
    app.state.session_maker = session_maker
    app.state.embedding_provider = embedding_provider
    app.state.llm_client = llm_client
    app.state.qdrant = qdrant

    logger.info("Embedding service started")

    try:
        yield
    finally:
        await embedding_provider.aclose()
        await llm_client.aclose()
        await qdrant.close()
        await engine.dispose()

        logger.info("Embedding service stopped")
