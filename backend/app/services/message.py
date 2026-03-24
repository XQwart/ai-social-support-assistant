from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.repositories.message import MessageRepository
    from app.models.message import Message, MessageRole


class MessageService:
    _message_repo: MessageRepository

    def __init__(self, message_repo: MessageRepository):
        self._message_repo = message_repo

    async def get_messages(
        self, chat_id: int, limit: int, offset: int, asc: bool = True
    ) -> list[Message]:
        messages = await self._message_repo.get_by_chat(chat_id, limit, offset, asc)

        return messages

    async def send_message(
        self, chat_id: int, message: str, role: MessageRole
    ) -> Message:
        return await self._message_repo.create(
            chat_id=chat_id, role=role, content=message
        )

    async def count_messages(self, chat_id: int) -> int:
        return await self._message_repo.count_messages_by_chat(chat_id)
