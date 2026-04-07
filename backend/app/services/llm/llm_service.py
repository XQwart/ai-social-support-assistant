from __future__ import annotations
from pathlib import Path
import json
import logging
from typing import TYPE_CHECKING

from app.core.constants import FAQ_JSON, CHUCK_JSON
from app.clients.base_clients import LLMClient
from .prompts import (
    build_system_prompt,
    COMPRESSED_CONTEXT_PREFIX,
    FALLBACK_EMPTY_RESPONSE,
    FALLBACK_AI_UNAVAILABLE,
    COMPRESS_CONTEXT_SYSTEM,
)

if TYPE_CHECKING:
    from app.core.config import Config


logger = logging.getLogger(__name__)


# TODO: Заменить json на qdrant
class LLMService:
    _config: Config
    _chat_client: LLMClient
    _compress_client: LLMClient

    def __init__(
        self, config: Config, chat_client: LLMClient, compress_client: LLMClient
    ):
        self._config = config
        self._chat_client = chat_client
        self._compress_client = compress_client

    def _load_knowledge_base(self) -> tuple[list[dict], list[dict]]:
        faq_data = self._load_json_file(FAQ_JSON, "faq.json")
        chuck_data = self._load_json_file(CHUCK_JSON, "chuck_data.json")

        return faq_data, chuck_data

    def _load_json_file(self, path: Path, label: str) -> list[dict]:
        try:
            if path.exists():
                content = path.read_text(encoding="utf-8")
                if content.strip():
                    return json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Не удалось загрузить %s: %s", label, e)

        return []

    async def generate_response(
        self,
        user_message: str,
        chat_history: list[dict[str, str]],
        compressed_context: str | None = None,
    ) -> str:
        logger.info(
            "Запрос к ИИ: user_message='%s', history_len=%d",
            user_message[:100],
            len(chat_history),
        )
        faq_data, chuck_data = self._load_knowledge_base()
        system_prompt = build_system_prompt(faq_data, chuck_data)

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if compressed_context:
            messages.append(
                {
                    "role": "system",
                    "content": (f"{COMPRESSED_CONTEXT_PREFIX}{compressed_context}"),
                }
            )
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        try:
            response_text = await self._chat_client.get_completion(
                messages,
                max_tokens=self._config.llm_generate_max_tokens,
                temperature=self._config.llm_generate_temperature,
            )
            if response_text:
                logger.info(
                    "ИИ успешно сгенерировал ответ (длина: %d)", len(response_text)
                )
                return response_text

            logger.warning("ИИ вернул пустой ответ")
            return FALLBACK_EMPTY_RESPONSE

        except Exception:
            logger.exception("Критическая ошибка при обращении к ИИ")
            return FALLBACK_AI_UNAVAILABLE

    async def compress_context(self, messages: list[dict[str, str]]) -> str:
        messages_text = "\n".join(
            f"{'Пользователь' if m['role'] == 'user' else 'Ассистент'}: {m['content']}"
            for m in messages
        )

        prepared_messages = [
            {"role": "system", "content": COMPRESS_CONTEXT_SYSTEM},
            {"role": "user", "content": messages_text},
        ]

        try:
            response = await self._compress_client.get_completion(
                prepared_messages,
                max_tokens=self._config.llm_compress_max_tokens,
                temperature=self._config.llm_compress_temperature,
            )
            return response or ""
        except Exception as e:
            logger.error("Ошибка сжатия контекста: %s", e)
            return messages_text[: self._config.llm_fallback_context_limit]
