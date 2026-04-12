from __future__ import annotations
from typing import TYPE_CHECKING

from app.models.message_model import MessageRole
from app.schemas.message_schemas import ConversationResult

if TYPE_CHECKING:
    from . import ChatService, MessageService, LLMService
    from app.core.config import Config
    from app.models import ChatModel, MessageModel


class ConversationService:
    _llm_service: LLMService
    _message_service: MessageService
    _chat_service: ChatService
    _config: Config

    def __init__(
        self,
        llm_service: LLMService,
        message_service: MessageService,
        chat_service: ChatService,
        config: Config,
    ):
        self._llm_service = llm_service
        self._message_service = message_service
        self._chat_service = chat_service
        self._config = config

    async def send_message(self, chat: ChatModel, content: str) -> ConversationResult:
        user_msg = await self._message_service.send_message(
            chat_id=chat.id, message=content, role=MessageRole.USER
        )

        chat_history, compressed_context, was_compressed = await self._prepare_context(
            chat=chat
        )
        ai_response = await self._llm_service.generate_response(
            user_message=content,
            chat_history=chat_history,
            compressed_context=compressed_context,
        )
        assistant_msg = await self._message_service.send_message(
            chat_id=chat.id, message=ai_response, role=MessageRole.ASSISTANT
        )

        await self._chat_service.update_chat(chat)

        return ConversationResult(
            user_message=user_msg,
            assistant_message=assistant_msg,
            context_compressed=was_compressed,
        )

    async def _prepare_context(
        self, chat: ChatModel
    ) -> tuple[list[dict[str, str]], str | None, bool]:
        messages_count = await self._message_service.count_messages(chat.id)
        mesasges_count_without_user = messages_count - 1
        if messages_count <= self._config.summary_limit:
            messages = await self._message_service.get_messages(
                chat_id=chat.id, limit=mesasges_count_without_user, offset=0
            )

            return self._to_history(messages), None, False

        if messages_count % self._config.summary_limit <= 1:
            messages = await self._message_service.get_messages(
                chat_id=chat.id, limit=self._config.context_size, offset=1, asc=False
            )
            compressed = await self._compress_and_save(chat, messages[::-1])

            return [], compressed, True

        messages = await self._message_service.get_messages(
            chat_id=chat.id,
            limit=self._config.summary_limit,
            offset=mesasges_count_without_user - self._config.summary_limit,
        )
        return self._to_history(messages), chat.compressed_context, False

    async def _compress_and_save(
        self, chat: ChatModel, messages: list[MessageModel]
    ) -> str:
        history = self._to_history(messages)
        compressed_context = await self._llm_service.compress_context(history)

        await self._chat_service.update_chat(
            chat=chat, compressed_context=compressed_context
        )

        return compressed_context

    def _to_history(self, messages: list[MessageModel]) -> list[dict[str, str]]:
        return [{"role": m.role.value, "content": m.content} for m in messages]
