from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from app.clients.base_clients import LLMClient, LLMCompletion
from .prompts import (
    build_system_prompt,
    COMPRESSED_CONTEXT_PREFIX,
    FALLBACK_EMPTY_RESPONSE,
    FALLBACK_AI_UNAVAILABLE,
    COMPRESS_CONTEXT_SYSTEM,
)

if TYPE_CHECKING:
    from app.core.config import Config
    from app.models import UserModel
    from app.schemas.rag_schemas import RetrievedChunk


logger = logging.getLogger(__name__)


class LLMService:
    _config: Config
    _chat_client: LLMClient
    _compress_client: LLMClient

    def __init__(
        self,
        config: Config,
        chat_client: LLMClient,
        compress_client: LLMClient,
    ):
        self._config = config
        self._chat_client = chat_client
        self._compress_client = compress_client

    async def generate_response(
        self,
        user: UserModel,
        user_message: str,
        chat_history: list[dict[str, str]],
        public_chunks: list[RetrievedChunk],
        internal_chunks: list[RetrievedChunk],
        compressed_context: str | None = None,
    ) -> LLMCompletion:
        logger.info(
            "Запрос к ИИ: user_id=%s, is_sber=%s, user_message='%s', history_len=%d, "
            "public_chunks=%d, internal_chunks=%d",
            user.id,
            user.is_sber_employee,
            user_message[:100],
            len(chat_history),
            len(public_chunks),
            len(internal_chunks),
        )
        system_prompt = build_system_prompt(user, public_chunks, internal_chunks)

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if compressed_context:
            messages.append(
                {
                    "role": "system",
                    "content": f"{COMPRESSED_CONTEXT_PREFIX}{compressed_context}",
                }
            )
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        try:
            completion = await self._chat_client.get_completion(
                messages,
                max_tokens=self._config.llm_generate_max_tokens,
                temperature=self._config.llm_generate_temperature,
            )
            if completion.text:
                logger.info(
                    "ИИ успешно сгенерировал ответ (длина: %d)", len(completion.text)
                )
                return completion

            logger.warning("ИИ вернул пустой ответ")
            return LLMCompletion(text=FALLBACK_EMPTY_RESPONSE, usage=completion.usage)

        except Exception:
            logger.exception("Критическая ошибка при обращении к ИИ")
            return LLMCompletion(text=FALLBACK_AI_UNAVAILABLE, usage=None)

    async def compress_context(
        self,
        messages: list[dict[str, str]],
        previous_summary: str | None = None,
    ) -> str:
        blocks: list[str] = []

        if previous_summary:
            blocks.append(f"Предыдущее резюме диалога:\n{previous_summary}")

        blocks.extend(
            f"{'Пользователь' if m['role'] == 'user' else 'Ассистент'}: {m['content']}"
            for m in messages
        )

        messages_text = "\n".join(blocks)
        prepared_messages = [
            {"role": "system", "content": COMPRESS_CONTEXT_SYSTEM},
            {"role": "user", "content": messages_text},
        ]

        try:
            completion = await self._compress_client.get_completion(
                prepared_messages,
                max_tokens=self._config.llm_compress_max_tokens,
                temperature=self._config.llm_compress_temperature,
            )
            return completion.text or ""

        except Exception as e:
            logger.error("Ошибка сжатия контекста: %s", e)
            return messages_text[: self._config.llm_fallback_context_limit]
