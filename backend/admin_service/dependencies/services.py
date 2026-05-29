from __future__ import annotations
from typing import Annotated

from fastapi import Depends

from admin_service.dependencies.config import AdminConfigDep
from admin_service.dependencies.http import ChunkApiClientDep
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
from admin_service.services.chunk_api_client import ChunkApiClient


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


def get_chunk_api_client(
    client: ChunkApiClientDep,
    config: AdminConfigDep,
) -> ChunkApiClient:
    return ChunkApiClient(client=client, base_url=config.chunk_api_url)


ChunkApiClientServiceDep = Annotated[ChunkApiClient, Depends(get_chunk_api_client)]


def get_chunk_admin_service(
    repo: AdminChunkRepoDep,
    api: ChunkApiClientServiceDep,
    audit: "AdminAuditServiceDep",
) -> ChunkAdminService:
    return ChunkAdminService(repo=repo, api=api, audit=audit)


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
