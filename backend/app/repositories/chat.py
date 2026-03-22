from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.chat import Chat

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ChatRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user_id: int, title: str) -> Chat:
        chat = Chat(user_id=user_id, title=title)
        self._session.add(chat)
        await self._session.commit()
        await self._session.refresh(chat)
        return chat

    async def get_by_id(self, chat_id: int) -> Chat | None:
        result = await self._session.execute(select(Chat).where(Chat.id == chat_id))
        return result.scalar_one_or_none()

    async def get_all_by_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> list[Chat]:
        result = await self._session.execute(
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete(self, chat_id: int) -> bool:
        chat = await self.get_by_id(chat_id)
        if chat is None:
            return False

        await self._session.delete(chat)
        await self._session.commit()
        return True
