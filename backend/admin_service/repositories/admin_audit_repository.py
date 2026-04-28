from __future__ import annotations
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from shared.models import AdminAuditLog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AdminAuditRepository:
    _session: "AsyncSession"

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session

    async def log(
        self,
        admin_id: int | None,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        payload_diff: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AdminAuditLog:
        entry = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload_diff=payload_diff,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def recent(self, limit: int = 50) -> list[AdminAuditLog]:
        result = await self._session.execute(
            select(AdminAuditLog)
            .order_by(AdminAuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
