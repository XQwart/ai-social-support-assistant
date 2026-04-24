from __future__ import annotations
from typing import Annotated

from fastapi import Depends

from admin_service.dependencies.session import DBSessionDep
from admin_service.repositories import (
    AdminAuditRepository,
    AdminChunkRepository,
    AdminPromptRepository,
    AdminRepository,
)


def get_admin_repo(session: DBSessionDep) -> AdminRepository:
    return AdminRepository(session)


def get_admin_audit_repo(session: DBSessionDep) -> AdminAuditRepository:
    return AdminAuditRepository(session)


def get_admin_prompt_repo(session: DBSessionDep) -> AdminPromptRepository:
    return AdminPromptRepository(session)


def get_admin_chunk_repo(session: DBSessionDep) -> AdminChunkRepository:
    return AdminChunkRepository(session)


AdminRepoDep = Annotated[AdminRepository, Depends(get_admin_repo)]
AdminAuditRepoDep = Annotated[
    AdminAuditRepository, Depends(get_admin_audit_repo)
]
AdminPromptRepoDep = Annotated[
    AdminPromptRepository, Depends(get_admin_prompt_repo)
]
AdminChunkRepoDep = Annotated[
    AdminChunkRepository, Depends(get_admin_chunk_repo)
]
