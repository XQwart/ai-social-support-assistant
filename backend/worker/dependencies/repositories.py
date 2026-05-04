from __future__ import annotations
from typing import Annotated

from fastapi import Depends, Request
from worker.repositories import ChunkRepository, VectorRepository
from worker.dependencies.session import SessionDep
from worker.repositories.source_reg_repository import SourceRegistrationRepository
from worker.repositories.source_crawl_repository import SourceCrawlRepository
from worker.repositories.region_repository import RegionRepository


def get_vector_repository(
    request: Request,
) -> VectorRepository:
    return VectorRepository(
        client=request.app.state.qdrant,
        chunks_collection_name=request.app.state.config.chunks_collection_name,
    )


def get_region_repository(session: SessionDep):
    return RegionRepository(session=session)


def get_source_crawl_repository(session: SessionDep):
    return SourceCrawlRepository(session=session)


def get_source_reg_repository(session: SessionDep):
    return SourceRegistrationRepository(session=session)


def get_chunk_repository(
    session: SessionDep,
) -> ChunkRepository:
    return ChunkRepository(session=session)


VectorRepositoryDep = Annotated[VectorRepository, Depends(get_vector_repository)]
ChunkRepositoryDep = Annotated[ChunkRepository, Depends(get_chunk_repository)]
SourceRegistrationRepositoryDep = Annotated[
    SourceRegistrationRepository, Depends(get_source_reg_repository)
]
SourceCrawlRepositoryDep = Annotated[
    SourceCrawlRepository, Depends(get_source_crawl_repository)
]

RegionRepositoryDep = Annotated[RegionRepository, Depends(get_region_repository)]
