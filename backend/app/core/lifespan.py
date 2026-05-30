import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.services.prompt_service import PromptService

from .agent import create_checkpointer, create_agent_tools_scope_factory
from .config import get_config
from .database import create_engine, create_session_maker
from .redis import create_redis
from .logger import setup_logging
from .http import create_sber_http_client, create_fetch_client, create_http_client
from .llm import create_llm_clients, create_embedding_client
from .qdrant import create_qdrant_client, ensure_collection
from shared.utils.pdf_extractor import PdfTextExtractor

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()

    setup_logging(level=config.log_level)

    pdf_extractor = PdfTextExtractor()

    engine = create_engine(config)
    session_maker = create_session_maker(engine)
    redis = create_redis(config)
    sber_client = create_sber_http_client(config)
    web_search_client = create_http_client(config)
    fetch_client = create_fetch_client(config)

    chat_llm_client, compress_llm_client = create_llm_clients(config)
    embedding_client, vector_size = create_embedding_client(config)

    checkpointer = await create_checkpointer(config)
    qdrant = create_qdrant_client(config)
    await ensure_collection(
        qdrant,
        collection_name=config.qdrant_collection,
        vector_size=vector_size,
        distance=config.rag_distance,
    )

    agent_tools_scope_factory = create_agent_tools_scope_factory(
        session_maker=session_maker,
        search_client=web_search_client,
        fetch_client=fetch_client,
        pdf_extractor=pdf_extractor,
        embedding_client=embedding_client,
        qdrant=qdrant,
        config=config,
    )

    prompt_service = PromptService(session_maker=session_maker, redis=redis)
    await prompt_service.start()

    app.state.db_engine = engine
    app.state.session_maker = session_maker
    app.state.checkpointer = checkpointer
    app.state.redis = redis
    app.state.sber_client = sber_client
    app.state.web_search_client = web_search_client
    app.state.fetch_client = fetch_client

    app.state.chat_llm_client = chat_llm_client
    app.state.compress_llm_client = compress_llm_client
    app.state.embedding_client = embedding_client
    app.state.qdrant = qdrant
    app.state.agent_tools_scope_factory = agent_tools_scope_factory
    app.state.pdf_extractor = pdf_extractor
    app.state.prompt_service = prompt_service

    logger.info("Application started successfully")

    try:
        yield
    finally:
        await prompt_service.stop()
        await checkpointer.conn.close()
        await sber_client.aclose()
        await web_search_client.aclose()
        await fetch_client.aclose()
        await qdrant.close()
        await redis.aclose()
        await engine.dispose()
