from __future__ import annotations
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from langchain.embeddings.base import Embeddings

from app.repositories import (
    ChunkRepository,
    DocumentRepository,
    RegionRepository,
    UserRepository,
)
from ..user_service import UserService
from ..rag_service import RAGService
from ..region_service import RegionService

if TYPE_CHECKING:
    from app.services import RegionService, RAGService, UserService

    from app.core.config import Config
    from app.services import (
        WebSearchService,
        PageFetchService,
    )
    from app.repositories import ChunkRepository


@dataclass(slots=True)
class AgentToolsScope:
    region_service: RegionService
    rag_service: RAGService
    user_service: UserService


class AgentToolsScopeFactory:
    _session_maker: async_sessionmaker[AsyncSession]
    _web_search_service: WebSearchService
    _page_fetch_service: PageFetchService
    _chunk_repo: ChunkRepository
    _embedding_client: Embeddings
    _config: Config

    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        web_search_service: WebSearchService,
        page_fetch_service: PageFetchService,
        chunk_repo: ChunkRepository,
        embedding_client: Embeddings,
        config: Config,
    ) -> None:
        self._session_maker = session_maker
        self._web_search_service = web_search_service
        self._page_fetch_service = page_fetch_service
        self._chunk_repo = chunk_repo
        self._embedding_client = embedding_client
        self._config = config

    @asynccontextmanager
    async def scope(self) -> AsyncIterator[AgentToolsScope]:
        async with self._session_maker() as session:
            # from app.services import RegionService, RAGService, UserService

            region_repo = RegionRepository(session)
            document_repo = DocumentRepository(session)
            user_repo = UserRepository(session)

            yield AgentToolsScope(
                region_service=RegionService(region_repo),
                rag_service=RAGService(
                    self._embedding_client, document_repo, self._chunk_repo
                ),
                user_service=UserService(user_repo),
            )

    @property
    def web_search_service(self) -> WebSearchService:
        return self._web_search_service

    @property
    def page_fetch_service(self) -> PageFetchService:
        return self._page_fetch_service
