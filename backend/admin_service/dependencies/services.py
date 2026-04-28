from __future__ import annotations
from typing import Annotated

from fastapi import Depends

from admin_service.dependencies.config import AdminConfigDep, BackendConfigDep
from admin_service.dependencies.embedding import EmbeddingClientDep
from admin_service.dependencies.qdrant import QdrantClientDep
from admin_service.dependencies.redis import RedisDep
from admin_service.dependencies.repositories import (
    AdminAuditRepoDep,
    AdminChunkRepoDep,
    AdminPromptRepoDep,
    AdminRepoDep,
)
from admin_service.dependencies.security import SessionTokenDep
from admin_service.services import (
    AdminAuditService,
    AdminAuthService,
    ChunkAdminService,
    PromptAdminService,
)


def get_admin_audit_service(repo: AdminAuditRepoDep) -> AdminAuditService:
    return AdminAuditService(repo)


def get_admin_auth_service(
    admin_repo: AdminRepoDep,
    audit: "AdminAuditServiceDep",
    token: SessionTokenDep,
    config: AdminConfigDep,
    redis: RedisDep,
) -> AdminAuthService:
    return AdminAuthService(
        admin_repo=admin_repo,
        audit=audit,
        token=token,
        config=config,
        redis=redis,
    )


def get_prompt_admin_service(
    repo: AdminPromptRepoDep,
    redis: RedisDep,
    audit: "AdminAuditServiceDep",
) -> PromptAdminService:
    return PromptAdminService(repo=repo, redis=redis, audit=audit)


def get_chunk_admin_service(
    repo: AdminChunkRepoDep,
    qdrant: QdrantClientDep,
    embedding: EmbeddingClientDep,
    audit: "AdminAuditServiceDep",
    config: BackendConfigDep,
) -> ChunkAdminService:
    return ChunkAdminService(
        repo=repo,
        qdrant=qdrant,
        embedding=embedding,
        audit=audit,
        collection=config.qdrant_collection,
    )


AdminAuditServiceDep = Annotated[
    AdminAuditService, Depends(get_admin_audit_service)
]
AdminAuthServiceDep = Annotated[
    AdminAuthService, Depends(get_admin_auth_service)
]
PromptAdminServiceDep = Annotated[
    PromptAdminService, Depends(get_prompt_admin_service)
]
ChunkAdminServiceDep = Annotated[
    ChunkAdminService, Depends(get_chunk_admin_service)
]
