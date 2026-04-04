from __future__ import annotations
from typing import TYPE_CHECKING

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from .llm_service_base import LLMServiceBase

if TYPE_CHECKING:
    from app.core.config import Config


class GigaChatService(LLMServiceBase[Messages]):
    _config: Config
    _client: GigaChat

    def __init__(self, config: Config):
        super().__init__(config)
        self._client = GigaChat(
            credentials=config.gigachat_api_key,
            ca_bundle_file=config.rus_root_ca_cert_path,
            scope=config.gigachat_scope,
            timeout=config.llm_timeout,
        )

    def _prepare_message(self, message: dict[str, str]) -> Messages:
        return Messages(role=MessagesRole(message["role"]), content=message["content"])

    async def _get_completion(
        self, messages: list[Messages], max_tokens: int = 512, temperature: float = 0.2
    ) -> str | None:
        response = await self._client.achat(
            Chat(
                model=self._config.gigachat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )

        return response.choices[0].message.content

    async def aclose(self) -> None:
        await self._client.aclose()
