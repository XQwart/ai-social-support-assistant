from __future__ import annotations
from typing import TYPE_CHECKING

import logging

if TYPE_CHECKING:
    from app.repositories.chat import ChatRepository
    from app.models.chat import Chat

logger = logging.getLogger(__name__)


class ChatService:
    _chat_rep: ChatRepository

    def __init__(
        self,
        chat_rep: ChatRepository,
    ):
        self._chat_rep = chat_rep

    async def create_chat(self, user_id: int, message: str) -> Chat:

        title = message[:255]

        return await self._chat_rep.create(user_id=user_id, title=title)

    async def get_chats(self, user_id: int) -> tuple[list[Chat], int]:

        chats = self._chat_rep.get_all_by_user(user_id=user_id)

        return chats, len(chats)

    async def delete_chat(self, chat_id: int) -> bool:

        return self._chat_rep.delete(chat_id=chat_id)

    async def get_chat(self, chat_id: int) -> Chat:

        return self._chat_rep.get_by_id(chat_id=chat_id)
