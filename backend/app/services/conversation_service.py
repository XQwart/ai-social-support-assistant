from __future__ import annotations
from typing import TYPE_CHECKING

from app.models.message_model import MessageRole
from app.schemas.message_schemas import ConversationResult

if TYPE_CHECKING:
    from . import (
        ChatService,
        ContextBudgetService,
        ContextStatsService,
        MessageService,
        LLMService,
        RAGService,
    )
    from app.core.config import Config
    from app.models import ChatModel, MessageModel
    from app.schemas.chat_schemas import ChatContextStats


class ConversationService:
    _llm_service: LLMService
    _message_service: MessageService
    _ctx_budget_service: ContextBudgetService
    _ctx_stats_service: ContextStatsService
    _chat_service: ChatService
    _rag_service: RAGService
    _config: Config

    def __init__(
        self,
        llm_service: LLMService,
        message_service: MessageService,
        ctx_budget_service: ContextBudgetService,
        ctx_stats_service: ContextStatsService,
        chat_service: ChatService,
        rag_service: RAGService,
        config: Config,
    ):
        self._llm_service = llm_service
        self._message_service = message_service
        self._ctx_budget_service = ctx_budget_service
        self._ctx_stats_service = ctx_stats_service
        self._chat_service = chat_service
        self._rag_service = rag_service
        self._config = config

    async def send_message(self, chat: ChatModel, content: str) -> ConversationResult:
        user_msg = await self._message_service.send_message(
            chat_id=chat.id, message=content, role=MessageRole.USER
        )

        ctx_stats = await self._ctx_stats_service.get_chat_stats(chat)
        chat_history, compressed_context, was_compressed = await self._prepare_context(
            chat=chat, ctx_stats=ctx_stats, current_user_message_id=user_msg.id
        )

        retrieved_chunks = await self._rag_service.retrieve(
            question=content, place_of_work=chat.user.place_of_work
        )
        chunks = [
            {
                "source_name": chunk.source_name,
                "source_url": chunk.source_url,
                "text": chunk.text,
            }
            for chunk in retrieved_chunks
        ]

        completion = await self._llm_service.generate_response(
            user_message=content,
            chat_history=chat_history,
            chunks=chunks,
            compressed_context=compressed_context,
        )

        usage_updates = self._ctx_budget_service.build_usage_updates(
            ctx_stats=ctx_stats,
            usage=completion.usage,
            was_compressed_before_request=was_compressed,
        )
        if usage_updates:
            await self._ctx_stats_service.update_chat_stats(chat, **usage_updates)

        assistant_msg = await self._message_service.send_message(
            chat_id=chat.id, message=completion.text or "", role=MessageRole.ASSISTANT
        )

        await self._chat_service.update_chat(chat)

        return ConversationResult(
            user_message=user_msg,
            assistant_message=assistant_msg,
            context_compressed=was_compressed,
        )

    async def _prepare_context(
        self, chat: ChatModel, ctx_stats: ChatContextStats, current_user_message_id: int
    ) -> tuple[list[dict[str, str]], str | None, bool]:
        unsummarized_messages = await self._message_service.get_messages_after_id(
            chat_id=chat.id,
            after_id=chat.compressed_up_to_message_id,
            before_id=current_user_message_id,
        )

        if not unsummarized_messages:
            return [], chat.compressed_context, False

        should_compress = self._ctx_budget_service.should_compress(ctx_stats)
        if not should_compress:
            return (
                self._to_history(unsummarized_messages),
                chat.compressed_context,
                False,
            )

        keep_msgs = self._config.llm_summary_keep_recent_messages
        if len(unsummarized_messages) <= keep_msgs:
            return (
                self._to_history(unsummarized_messages),
                chat.compressed_context,
                False,
            )

        messages_to_compress = unsummarized_messages[:-keep_msgs]

        compressed = await self._compress_and_save(
            chat=chat,
            messages=messages_to_compress,
            compressed_up_to_message_id=messages_to_compress[-1].id,
        )

        return self._to_history(unsummarized_messages[-keep_msgs:]), compressed, True

    async def _compress_and_save(
        self,
        chat: ChatModel,
        messages: list[MessageModel],
        compressed_up_to_message_id: int,
    ) -> str:
        history = self._to_history(messages)
        compressed_context = await self._llm_service.compress_context(
            history, previous_summary=chat.compressed_context
        )

        await self._chat_service.update_chat(
            chat=chat,
            compressed_context=compressed_context,
            compressed_up_to_message_id=compressed_up_to_message_id,
        )

        return compressed_context

    def _to_history(self, messages: list[MessageModel]) -> list[dict[str, str]]:
        return [{"role": m.role.value, "content": m.content} for m in messages]
