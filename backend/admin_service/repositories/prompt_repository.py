from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select

from shared.models import Prompt, PromptHistory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AdminPromptRepository:
    """Write-side repository for editable prompts.

    Each ``update()`` is a single transaction that: reads the current
    row, writes a :class:`PromptHistory` snapshot of the old body, and
    overwrites the :class:`Prompt` with the new body + incremented
    version. Callers are expected to ``await session.commit()`` after a
    successful return.
    """

    _session: "AsyncSession"

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session

    async def list_all(self) -> list[Prompt]:
        result = await self._session.execute(
            select(Prompt).order_by(Prompt.key.asc())
        )
        return list(result.scalars().all())

    async def get_by_key(self, key: str) -> Prompt | None:
        result = await self._session.execute(
            select(Prompt).where(Prompt.key == key)
        )
        return result.scalar_one_or_none()

    async def get_history(self, key: str, limit: int = 50) -> list[PromptHistory]:
        result = await self._session.execute(
            select(PromptHistory)
            .where(PromptHistory.prompt_key == key)
            .order_by(PromptHistory.changed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self,
        key: str,
        new_body: str,
        admin_id: int,
    ) -> Prompt:
        current = await self.get_by_key(key)
        if current is None:
            raise KeyError(key)

        history = PromptHistory(
            prompt_key=current.key,
            body=current.body,
            version=current.version,
            changed_by=admin_id,
        )
        self._session.add(history)

        current.body = new_body
        current.version = current.version + 1
        current.updated_by = admin_id

        await self._session.flush()
        await self._session.refresh(current)
        return current

    async def seed_if_missing(
        self,
        key: str,
        body: str,
        description: str | None = None,
    ) -> bool:
        existing = await self.get_by_key(key)
        if existing is not None:
            return False
        prompt = Prompt(
            key=key,
            body=body,
            description=description,
            version=1,
        )
        self._session.add(prompt)
        await self._session.flush()
        return True
