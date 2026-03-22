from __future__ import annotations
from typing import TYPE_CHECKING

from app.models.message import MessageRole

if TYPE_CHECKING:
    from app.repositories.message import MessageRepository
    from app.models.message import Message


class MessageService:
    _message_repo: MessageRepository

    def __init__(self, message_repo: MessageRepository):
        self._message_repo = message_repo

    async def get_all_messages(
        self, chat_id: int, limit: int, offset: int
    ) -> list[Message]:
        messages = await self._message_repo.get_all_by_chat(chat_id, limit, offset)

        return messages

    async def send_message(self, chat_id: int, message: str) -> Message:
        return await self._message_repo.create(
            chat_id=chat_id, role=MessageRole.USER, content=message
        )
