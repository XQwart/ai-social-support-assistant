from __future__ import annotations
from typing import TYPE_CHECKING

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain.embeddings.base import Embeddings
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import httpx
from qdrant_client import AsyncQdrantClient

from app.services.agent import AgentToolsScopeFactory
from app.services import WebSearchService, PageFetchService
from app.repositories import ChunkRepository

if TYPE_CHECKING:
    from app.core.config import Config
    from shared.utils.pdf_extractor import PdfTextExtractor


async def create_checkpointer(config: Config) -> AsyncPostgresSaver:
    pool = AsyncConnectionPool(
        conninfo=config.database_url.replace("postgresql+asyncpg://", "postgresql://"),
        max_size=config.checkpointer_pool_max_conn,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await pool.open()

    checkpointer = AsyncPostgresSaver(conn=pool)
    await checkpointer.setup()

    return checkpointer


def create_agent_tools_scope_factory(
    session_maker: async_sessionmaker[AsyncSession],
    search_client: httpx.AsyncClient,
    fetch_client: httpx.AsyncClient,
    pdf_extractor: PdfTextExtractor,
    embedding_client: Embeddings,
    qdrant: AsyncQdrantClient,
    config: Config,
) -> AgentToolsScopeFactory:
    web_search = WebSearchService(search_client, config)
    page_fetch = PageFetchService(fetch_client, pdf_extractor, config)
    chunk_repo = ChunkRepository(qdrant, config)

    return AgentToolsScopeFactory(
        session_maker=session_maker,
        web_search_service=web_search,
        page_fetch_service=page_fetch,
        chunk_repo=chunk_repo,
        embedding_client=embedding_client,
        config=config,
    )
