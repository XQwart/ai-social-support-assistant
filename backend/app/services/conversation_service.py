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

        response = await self._agent_service.run(
            chat_id=chat.id, user=chat.user, content=content
        )

        assistant_msg = await self._message_service.send_message(
            chat_id=chat.id, message=response, role=MessageRole.ASSISTANT
        )

        await self._chat_service.update_chat(chat)

        return ConversationResult(
            user_message=user_msg,
            assistant_message=assistant_msg,
        )

    # async def send_message(self, chat: ChatModel, content: str) -> ConversationResult:
    #     user_msg = await self._message_service.send_message(
    #         chat_id=chat.id, message=content, role=MessageRole.USER
    #     )

    #     ctx_stats = await self._ctx_stats_service.get_chat_stats(chat)
    #     chat_history, compressed_context, was_compressed =
    # await self._prepare_context(
    #         chat=chat, ctx_stats=ctx_stats, current_user_message_id=user_msg.id
    #     )

    #     user = chat.user
    #     region_code = await self._region_service.get_code_by_name(
    #         user.region_current or user.region_reg
    #     )  # TODO: Исправить временное решение
    #     retrieved_chunks = await self._rag_service.retrieve(
    #         question=content, region=region_code, place_of_work=user.place_of_work
    #     )

    #     public_chunks = [c for c in retrieved_chunks if not c.is_internal]
    #     internal_chunks = (
    #         [c for c in retrieved_chunks if c.is_internal]
    #         if user.is_sber_employee
    #         else []
    #     )

    #     completion = await self._llm_service.generate_response(
    #         user=user,
    #         user_message=content,
    #         chat_history=chat_history,
    #         public_chunks=public_chunks,
    #         internal_chunks=internal_chunks,
    #         compressed_context=compressed_context,
    #     )

    #     clean_response, extraction = self._split_response_and_memory(
    #         completion.text or ""
    #     )
    #     if extraction.has_updates:
    #         await self._try_update_user_memory(user=user, extraction=extraction)

    #     usage_updates = self._ctx_budget_service.build_usage_updates(
    #         ctx_stats=ctx_stats,
    #         usage=completion.usage,
    #         was_compressed_before_request=was_compressed,
    #     )
    #     if usage_updates:
    #         await self._ctx_stats_service.update_chat_stats(chat, **usage_updates)

    #     assistant_msg = await self._message_service.send_message(
    #         chat_id=chat.id, message=clean_response, role=MessageRole.ASSISTANT
    #     )

    #     await self._chat_service.update_chat(chat)

    #     return ConversationResult(
    #         user_message=user_msg,
    #         assistant_message=assistant_msg,
    #         context_compressed=was_compressed,
    #     )
