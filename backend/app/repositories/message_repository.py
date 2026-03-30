from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select, func

from app.models import MessageModel

if TYPE_CHECKING:
    from app.models.message_model import MessageRole
    from sqlalchemy.ext.asyncio import AsyncSession


class MessageRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, chat_id: int, role: MessageRole, content: str
    ) -> MessageModel:
        message = MessageModel(chat_id=chat_id, role=role, content=content)
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def get_by_id(self, message_id: int) -> MessageModel | None:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.id == message_id)
        )
        return result.scalar_one_or_none()

    async def count_messages_by_chat(self, chat_id) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(MessageModel)
            .where(MessageModel.chat_id == chat_id)
        )

        return result.scalar_one()

    async def get_by_chat(
        self, chat_id: int, limit: int = 100, offset: int = 0, asc: bool = True
    ) -> list[MessageModel]:
        order_by = (
            MessageModel.created_at.asc() if asc else MessageModel.created_at.desc()
        )

        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.chat_id == chat_id)
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
