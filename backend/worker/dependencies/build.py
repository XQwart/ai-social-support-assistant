from __future__ import annotations

import logging
import asyncio
from redis import Redis
from threading import Lock
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client.models import VectorParams, Distance
from contextlib import asynccontextmanager
from worker.core.config import get_config, Config
from worker.services.embedding.build import build_embedding_provider
from worker.db.qdrant import create_qdrant
from worker.db.session import create_session
from worker.repositories import (
    ChunkRepository,
    VectorRepository,
    SourceRegistrationRepository,
    SourceCrawlRepository,
    RegionRepository,
)
from worker.services.parsing import (
    DocumentParsingService,
    HtmlLinkExtractor,
    HtmlTextExtractor,
    PdfTextExtractor,
    WebPageFetcher,
)
from worker.services.source import (
    SourceRegistrationService,
    SourceCrawlService,
    RegionService,
)
from worker.services.embedding.embedding_service import EmbeddingService
from worker.services.document_service import DocumentService
from worker.services.chunk_service import ChunkingService
from worker.services.processing_service import SourceProcessingService
from worker.services.discovery_service import LinkDiscoveryService
from worker.services.region_import_service import RegionSourceImportService
from worker.services.runtime_state_service import RuntimeStateService
from worker.services.quests_service import ChunkQuestionLLMService
from worker.services.llm.build import build_llm_client

logger = logging.getLogger(__name__)
_lock = Lock()


class WorkerDependencies:
    _instance: WorkerDependencies | None = None
    _init_lock: asyncio.Lock | None = None

    def __init__(self, config: Config) -> None:
        self._config = config

    @classmethod
    def _get_init_lock(cls) -> asyncio.Lock:
        if cls._init_lock is None:
            cls._init_lock = asyncio.Lock()
        return cls._init_lock

    async def _ainit(self) -> None:
        self._provider = build_embedding_provider(config=self._config)
        self._qdrant = create_qdrant(url=self._config.qdrant_url)
        self._llm_client = build_llm_client(config=self._config)
        self._quest_service = ChunkQuestionLLMService(llm_client=self._llm_client)

        self._redis = Redis.from_url(
            self._config.redis_celery_url,
            decode_responses=True,
        )
        self._runtime_state_service = RuntimeStateService(redis_client=self._redis)

        await self.ensure_collections(self._provider.vector_size)

        self._sessionmaker = create_session(self._config.database_url)
        self._fetcher = WebPageFetcher(default_timeout=self._config.default_timeout)
        self._text_extractor = HtmlTextExtractor()
        self._link_extractor = HtmlLinkExtractor()
        self._pdf_extractor = PdfTextExtractor()

        self._parsing_service = DocumentParsingService(
            fetcher=self._fetcher,
            text_extractor=self._text_extractor,
            pdf_extractor=self._pdf_extractor,
        )

        self._chunking_service = ChunkingService(
            embedding_model=self._config.polza_ai_embedding_model,
        )
        self._embedding_service = EmbeddingService(
            provider=self._provider,
            model=self._config.polza_ai_embedding_model,
        )

        logger.info("WorkerDependencies инициализированы")

    @asynccontextmanager
    async def session_scope(self) -> AsyncIterator[AsyncSession]:
        session = self._sessionmaker()

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @classmethod
    async def get(cls) -> WorkerDependencies:
        if cls._instance is None:
            with _lock:
                instance_missing = cls._instance is None
            if instance_missing:
                config = get_config()
                instance = cls(config)
                await instance._ainit()
                with _lock:
                    if cls._instance is None:
                        cls._instance = instance

        if cls._instance is None:
            raise RuntimeError("WorkerDependencies is not initialized")

        return cls._instance

    @classmethod
    async def reset(cls) -> None:
        with _lock:
            instance = cls._instance
            cls._instance = None

        if instance is not None:
            await instance._close()

    @property
    def runtime_state_service(self) -> RuntimeStateService:
        return self._runtime_state_service

    def build_processing_service(
        self, session: AsyncSession
    ) -> SourceProcessingService:

        vector_rep = VectorRepository(
            client=self._qdrant,
            questions_collection_name=self._config.questions_collection_name,
            chunks_collection_name=self._config.chunks_collection_name,
        )
        chunk_rep = ChunkRepository(session=session)
        document_service = DocumentService(
            vector_rep=vector_rep,
            chunk_rep=chunk_rep,
        )
        source_rep = SourceCrawlRepository(session=session)
        source_service = SourceCrawlService(source_repository=source_rep)

        return SourceProcessingService(
            parsing_service=self._parsing_service,
            embedding_service=self._embedding_service,
            document_service=document_service,
            chunking_service=self._chunking_service,
            quest_service=self._quest_service,
            source_service=source_service,
        )

    def build_region_source_import_service(self, session):
        region_rep = RegionRepository(session=session)
        region_service = RegionService(region_repository=region_rep)

        source_repository = SourceRegistrationRepository(session=session)
        source_service = SourceRegistrationService(source_repository=source_repository)

        link_service = LinkDiscoveryService(
            fetcher=self._fetcher,
            link_extractor=self._link_extractor,
            source_registration_service=source_service,
        )

        return RegionSourceImportService(
            region_service=region_service,
            source_registration_service=source_service,
            link_discovery_service=link_service,
        )

    async def ensure_collections(self, vector_size: int) -> None:
        await self._ensure_collection(
            collection_name=self._config.chunks_collection_name,
            vector_size=vector_size,
        )
        await self._ensure_collection(
            collection_name=self._config.questions_collection_name,
            vector_size=vector_size,
        )

    async def _ensure_collection(
        self,
        collection_name: str,
        vector_size: int,
    ) -> None:
        exists = await self._qdrant.collection_exists(collection_name)
        if exists:
            logger.info("Qdrant collection already exists: %s", collection_name)
            return

        await self._qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Qdrant collection created: %s", collection_name)

    async def _close(self) -> None:
        try:
            self._parsing_service.close()
        except Exception:
            pass
        try:
            await self._qdrant.close()
        except Exception:
            pass
        try:
            await self._provider.aclose()
        except Exception:
            pass
        try:
            await self._llm_client.aclose()
        except Exception:
            pass
        logger.info("WorkerDependencies закрыты")
