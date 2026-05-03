from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from worker.core.config import Config, get_config
from worker.db.session import create_session
from worker.repositories import (
    SourceCrawlRepository,
    SourceRegistrationRepository,
    RegionRepository,
)
from worker.services.parsing import (
    DocumentParsingService,
    HtmlLinkExtractor,
    HtmlTextExtractor,
    PdfTextExtractor,
    WebPageFetcher,
)
from worker.services.discovery_service import LinkDiscoveryService
from worker.services.region_import_service import RegionSourceImportService
from worker.services.source import (
    RegionService,
    SourceCrawlService,
    SourceRegistrationService,
)

logger = logging.getLogger(__name__)


class WorkerDependencies:
    def __init__(self, config: Config) -> None:
        self._config = config

    @classmethod
    async def create(cls, config: Config | None = None) -> "WorkerDependencies":
        instance = cls(config or get_config())
        await instance._ainit()
        return instance

    async def _ainit(self) -> None:
        self._sessionmaker = create_session(self._config.database_url)

        self._fetcher = WebPageFetcher(
            default_timeout=self._config.default_timeout,
        )
        self._text_extractor = HtmlTextExtractor()
        self._link_extractor = HtmlLinkExtractor()
        self._pdf_extractor = PdfTextExtractor()

        self._parsing_service = DocumentParsingService(
            fetcher=self._fetcher,
            text_extractor=self._text_extractor,
            pdf_extractor=self._pdf_extractor,
        )

        self._http_client = httpx.AsyncClient(
            timeout=300.0,
        )

        logger.info("WorkerDependencies initialized")

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
            session.expunge_all()
            await session.close()

    @property
    def parsing_service(self) -> DocumentParsingService:
        return self._parsing_service

    @property
    def http_client(self) -> httpx.AsyncClient:
        return self._http_client

    @property
    def processing_url(self) -> str:
        return self._config.processing_service_url

    def build_source_crawl_service(
        self,
        session: AsyncSession,
    ) -> SourceCrawlService:
        repo = SourceCrawlRepository(session=session)
        return SourceCrawlService(source_repository=repo)

    def build_source_registration_service(
        self,
        session: AsyncSession,
    ) -> SourceRegistrationService:
        repo = SourceRegistrationRepository(session=session)
        return SourceRegistrationService(source_repository=repo)

    def build_region_service(
        self,
        session: AsyncSession,
    ) -> RegionService:
        repo = RegionRepository(session=session)
        return RegionService(region_repository=repo)

    def build_region_source_import_service(
        self,
        session: AsyncSession,
    ) -> RegionSourceImportService:
        region_service = self.build_region_service(session)
        source_service = self.build_source_registration_service(session)

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

    async def aclose(self) -> None:
        try:
            await self._parsing_service.aclose()
        except Exception:
            logger.exception("Failed to close parsing service")

        try:
            await self._http_client.aclose()
        except Exception:
            logger.exception("Failed to close http client")

        try:
            engine = self._sessionmaker.kw.get("bind")
            if engine:
                await engine.dispose()
        except Exception:
            logger.exception("Failed to dispose SQLAlchemy engine")

        logger.info("WorkerDependencies closed")
