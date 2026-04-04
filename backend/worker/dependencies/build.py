from __future__ import annotations

import logging
from threading import Lock
from qdrant_client.models import VectorParams, Distance
from contextlib import contextmanager
from worker.core.config import get_config, Config
from worker.services.embedding.build import build_embedding_provider
from worker.db.qdrant import create_qdrant
from worker.db.session import create_session
from worker.repositories.chunk_repository import ChunkRepository
from worker.repositories.vector_repository import VectorRepository
from worker.services.parsing_service import ParsingService
from worker.services.embedding.embedding_service import EmbeddingService
from worker.services.document_service import DocumentService
from worker.services.chunk_service import ChunkingService
from worker.services.source_processing_service import SourceProcessingService
from worker.repositories.source_repository import SourceRepository
from worker.services.source_service import SourceService

logger = logging.getLogger(__name__)
_lock = Lock()


class WorkerDependencies:
    _instance: WorkerDependencies | None = None

    def __init__(self, config: Config) -> None:
        self._config = config

        self._provider = build_embedding_provider(config=config)
        self._qdrant = create_qdrant(url=config.qdrant_url)

        self.ensure_collection(self._provider.vector_size)

        self._sessionmaker = create_session(config.database_url)

        self._parsing_service = ParsingService(
            default_timeout=config.default_timeout,
        )
        self._chunking_service = ChunkingService(
            embedding_model=config.polza_ai_embedding_model,
        )
        self._embedding_service = EmbeddingService(
            provider=self._provider,
            model=config.polza_ai_embedding_model,
        )

        logger.info("WorkerDependencies инициализированы")

    @contextmanager
    def session_scope(self):
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def get(cls) -> WorkerDependencies:
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    config = get_config()
                    cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        with _lock:
            if cls._instance is not None:
                cls._instance._close()
                cls._instance = None

    def build_processing_service(self, session) -> SourceProcessingService:

        vector_rep = VectorRepository(
            client=self._qdrant,
            collection_name=self._config.qdrant_collection,
        )
        chunk_rep = ChunkRepository(session=session)
        document_service = DocumentService(
            vector_rep=vector_rep,
            chunk_rep=chunk_rep,
        )
        source_rep = SourceRepository(session=session)
        source_service = SourceService(source_repository=source_rep)

        return SourceProcessingService(
            parsing_service=self._parsing_service,
            embedding_service=self._embedding_service,
            document_service=document_service,
            chunking_service=self._chunking_service,
            source_service=source_service,
        )

    def ensure_collection(self, vector_size: int) -> None:
        if not self._qdrant.collection_exists(self._config.qdrant_collection):
            self._qdrant.create_collection(
                collection_name=self._config.qdrant_collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def _close(self) -> None:
        try:
            self._parsing_service.close()
        except Exception:
            pass
        try:
            self._qdrant.close()
        except Exception:
            pass
        try:
            self._provider.close()
        except Exception:
            pass
        logger.info("WorkerDependencies закрыты")
