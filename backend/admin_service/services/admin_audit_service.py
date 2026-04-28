from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any

from admin_service.middlewares.audit_context import (
    admin_id_ctx,
    client_ip_ctx,
    user_agent_ctx,
)

if TYPE_CHECKING:
    from admin_service.repositories.admin_audit_repository import (
        AdminAuditRepository,
    )


logger = logging.getLogger(__name__)


class AdminAuditService:
    """Thin façade over :class:`AdminAuditRepository`.

    Pulls IP/UA/admin_id from contextvars populated by the
    :class:`AuditContextMiddleware` so callers can log actions with a
    single keyword call. Best-effort — failures are logged and swallowed
    so a broken audit table does not block a legitimate write.
    """

    _repo: "AdminAuditRepository"

    def __init__(self, repo: "AdminAuditRepository") -> None:
        self._repo = repo

    async def record(
        self,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        payload_diff: dict[str, Any] | None = None,
        admin_id: int | None = None,
    ) -> None:
        try:
            await self._repo.log(
                admin_id=admin_id if admin_id is not None else admin_id_ctx.get(),
                action=action,
                target_type=target_type,
                target_id=target_id,
                payload_diff=payload_diff,
                ip_address=client_ip_ctx.get(),
                user_agent=user_agent_ctx.get(),
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "AdminAuditService: failed to record action=%s target=%s/%s",
                action,
                target_type,
                target_id,
            )
