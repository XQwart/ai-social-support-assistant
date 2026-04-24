from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select

from shared.models import Prompt

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PromptRepository:
    """Read-side repository for editable LLM prompts.

    The admin panel owns the write side (via its own
    ``AdminPromptRepository``); this class is used by the backend to
    warm and reconcile the :class:`app.services.PromptService` cache.
    """

    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Prompt]:
        result = await self._session.execute(select(Prompt))
        return list(result.scalars().all())

    async def get_one(self, key: str) -> Prompt | None:
        result = await self._session.execute(select(Prompt).where(Prompt.key == key))
        return result.scalar_one_or_none()

    async def get_versions(self) -> dict[str, int]:
        """Return a {key: version} map. Used for periodic reconcile."""
        result = await self._session.execute(select(Prompt.key, Prompt.version))
        return {row[0]: row[1] for row in result.all()}
