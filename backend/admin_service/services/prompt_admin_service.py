from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from app.services.prompt_service import PROMPT_INVALIDATION_CHANNEL

if TYPE_CHECKING:
    from redis.asyncio import Redis

    from shared.models import Prompt, PromptHistory

    from admin_service.repositories.prompt_repository import AdminPromptRepository
    from admin_service.services.admin_audit_service import AdminAuditService


logger = logging.getLogger(__name__)


class PromptValidationError(Exception):
    """Raised when a submitted prompt body fails server-side validation."""


class PromptAdminService:
    """Read+write service for the prompt admin UI.

    The write path (``update``) does three things in order:

    1. Persist the new body via :class:`AdminPromptRepository`, which
       atomically inserts a :class:`PromptHistory` snapshot and bumps
       the version.
    2. Publish the key to the ``prompts:invalidate`` Redis channel so
       every backend instance refreshes its cached body for that key.
    3. Append an audit-log entry recording the diff.

    Steps 2 and 3 are best-effort — failure does not roll back the
    database write. The 5-minute reconcile loop in
    :class:`app.services.PromptService` will recover from a missed
    invalidation.
    """

    _repo: "AdminPromptRepository"
    _redis: "Redis"
    _audit: "AdminAuditService"

    def __init__(
        self,
        repo: "AdminPromptRepository",
        redis: "Redis",
        audit: "AdminAuditService",
    ) -> None:
        self._repo = repo
        self._redis = redis
        self._audit = audit

    async def list_all(self) -> list["Prompt"]:
        return await self._repo.list_all()

    async def get(self, key: str) -> "Prompt | None":
        return await self._repo.get_by_key(key)

    async def get_history(self, key: str) -> list["PromptHistory"]:
        return await self._repo.get_history(key)

    async def update(
        self,
        key: str,
        new_body: str,
        admin_id: int,
    ) -> "Prompt":
        body = (new_body or "").strip("\r\n")
        self._validate(key, body)

        previous = await self._repo.get_by_key(key)
        if previous is None:
            raise KeyError(key)

        prev_body = previous.body
        prev_version = previous.version

        updated = await self._repo.update(
            key=key,
            new_body=body,
            admin_id=admin_id,
        )

        try:
            await self._redis.publish(PROMPT_INVALIDATION_CHANNEL, key)
        except Exception:  # noqa: BLE001
            logger.exception(
                "PromptAdminService: failed to publish invalidation for key=%s",
                key,
            )

        await self._audit.record(
            action="prompt.updated",
            target_type="prompt",
            target_id=key,
            admin_id=admin_id,
            payload_diff={
                "previous_version": prev_version,
                "new_version": updated.version,
                "previous_length": len(prev_body),
                "new_length": len(updated.body),
            },
        )
        return updated

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate(key: str, body: str) -> None:
        if not body:
            raise PromptValidationError("Тело промпта не может быть пустым.")
        if len(body) > 32_000:
            raise PromptValidationError(
                "Слишком длинный промпт: ограничение 32000 символов."
            )
        if key == "COMPRESS_CONTEXT_SYSTEM" and "{messages}" not in body:
            raise PromptValidationError(
                "Промпт COMPRESS_CONTEXT_SYSTEM должен содержать плейсхолдер "
                "{messages}."
            )
