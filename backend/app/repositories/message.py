from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select, func

from app.models.message import Message, MessageRole

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class MessageRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, chat_id: int, role: MessageRole, content: str) -> Message:
        message = Message(chat_id=chat_id, role=role, content=content)
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def get_by_id(self, message_id: int) -> Message | None:
        result = await self._session.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def count_messages_by_chat(self, chat_id) -> int:
        result = await self._session.execute(
            select(func.count).select_from(Message).where(Message.chat_id == chat_id)
        )

        return result.scalar()

    async def get_by_chat(
        self, chat_id: int, limit: int = 100, offset: int = 0, asc: bool = True
    ) -> list[Message]:
        order_by = Message.created_at.asc() if asc else Message.created_at.desc()

        result = await self._session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(order_by)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete(self, message_id: int) -> bool:
        message = await self.get_by_id(message_id)
        if message is None:
            return False

        await self._session.delete(message)
        await self._session.commit()
        return True
