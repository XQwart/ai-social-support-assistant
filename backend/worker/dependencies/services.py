from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from worker.dependencies.repositories import (
    VectorRepositoryDep,
    ChunkRepositoryDep,
    SourceCrawlRepositoryDep,
    SourceRegistrationRepositoryDep,
    RegionRepositoryDep,
)
from worker.services.chunk_index_service import ChunkIndexingService
from worker.services.chunk_service import ChunkingService
from worker.services.embedding.embedding_service import EmbeddingService
from worker.services.quests_service import ChunkQuestionLLMService
from worker.services.chunk_manager_service import ChunkManagementService
from worker.services.document_service import DocumentService
from worker.services.source.region_service import RegionService
from worker.services.source.source_registration_service import SourceRegistrationService
from worker.services.source.source_crawl_service import SourceCrawlService


def get_chunking_service(request: Request) -> ChunkingService:
    return ChunkingService(
        embedding_model=request.app.state.embedding_model,
    )


def get_embedding_service(request: Request) -> EmbeddingService:
    return EmbeddingService(
        provider=request.app.state.embedding_provider,
    )


def get_quest_service(request: Request) -> ChunkQuestionLLMService:
    return ChunkQuestionLLMService(llm_client=request.app.state.llm_client)


def get_chunk_indexing_service(
    embedding_service: EmbeddingServiceDep,
    quest_service: QuestServiceDep,
) -> ChunkIndexingService:
    return ChunkIndexingService(
        embedding_service=embedding_service,
        quest_service=quest_service,
    )


def get_document_service(
    vector_rep: VectorRepositoryDep, chunk_rep: ChunkRepositoryDep
):
    return DocumentService(vector_rep=vector_rep, chunk_rep=chunk_rep)


def get_region_service(region_rep: RegionRepositoryDep):
    return RegionService(region_rep)


def get_source_crawl(source_crawl: SourceCrawlRepositoryDep):
    return SourceCrawlService(source_repository=source_crawl)


def get_source_reg(source_reg: SourceRegistrationRepositoryDep):
    return SourceRegistrationService(source_reg)


def get_chunk_managmet_service(
    doc_service: DocumentServiceDep,
    chunk_servce: ChunkingServiceDep,
    reg_service: RegionServiceDep,
    source_service: SourceRegistrationServiceDep,
    chunk_index_service: ChunkIndexingServiceDep,
):
    return ChunkManagementService(
        document_service=doc_service,
        chunking_service=chunk_servce,
        source_service=source_service,
        chunk_indexing_service=chunk_index_service,
        region_service=reg_service,
    )


ChunkingServiceDep = Annotated[ChunkingService, Depends(get_chunking_service)]
EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]
QuestServiceDep = Annotated[ChunkQuestionLLMService, Depends(get_quest_service)]
ChunkIndexingServiceDep = Annotated[
    ChunkIndexingService, Depends(get_chunk_indexing_service)
]
SourceRegistrationServiceDep = Annotated[
    SourceRegistrationService, Depends(get_source_reg)
]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
RegionServiceDep = Annotated[RegionService, Depends(get_region_service)]
ChunkManagementServiceDep = Annotated[
    ChunkManagementService, Depends(get_chunk_managmet_service)
]
