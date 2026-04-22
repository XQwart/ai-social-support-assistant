from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from app.models.message_model import MessageRole
from app.schemas.message_schemas import ConversationResult

if TYPE_CHECKING:
    from . import (
        AgentService,
        ChatService,
        MessageService,
        RAGService,
        UserService,
        RegionService,
    )
    from app.core.config import Config
    from app.models import ChatModel


logger = logging.getLogger(__name__)


class ConversationService:
    _agent_service: AgentService
    _message_service: MessageService
    _chat_service: ChatService
    _rag_service: RAGService
    _user_service: UserService
    _region_service: RegionService
    _config: Config

    def __init__(
        self,
        agent_service: AgentService,
        message_service: MessageService,
        chat_service: ChatService,
        rag_service: RAGService,
        user_service: UserService,
        region_service: RegionService,
        config: Config,
    ):
        self._agent_service = agent_service
        self._message_service = message_service
        self._chat_service = chat_service
        self._rag_service = rag_service
        self._user_service = user_service
        self._region_service = region_service
        self._config = config

    async def send_message(self, chat: ChatModel, content: str) -> ConversationResult:
        user_msg = await self._message_service.send_message(
            chat_id=chat.id, message=content, role=MessageRole.USER
        )

        messages_count = await self._message_service.count_messages(chat.id)
        response = await self._agent_service.run(
            chat_id=chat.id,
            user=chat.user,
            content=content,
            is_new_dialog=messages_count <= 2,
        )

        assistant_msg = await self._message_service.send_message(
            chat_id=chat.id, message=response, role=MessageRole.ASSISTANT
        )

        await self._chat_service.update_chat(chat)

        return ConversationResult(
            user_message=user_msg,
            assistant_message=assistant_msg,
        )
