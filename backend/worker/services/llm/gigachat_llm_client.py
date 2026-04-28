from __future__ import annotations

from gigachat.models import Chat, Messages, MessagesRole
from gigachat import GigaChat

from worker.client.base_clients import LLMClient
from worker.core.config import Config


class GigaChatLLMClient(LLMClient):
    def __init__(self, config: Config, model_name: str | None) -> None:
        self._model_name = model_name
        self._client = GigaChat(
            credentials=config.gigachat_api_key,
            ca_bundle_file=config.rus_root_ca_cert_path,
            scope=config.gigachat_scope,
            timeout=config.llm_timeout,
            model=model_name,
        )

    async def get_completion_text(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        prepared_messages = [
            Messages(
                role=MessagesRole(message["role"]),
                content=message["content"],
            )
            for message in messages
        ]

        response = await self._client.achat(
            Chat(
                messages=prepared_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )

        return response.choices[0].message.content or ""

    async def aclose(self) -> None:
        await self._client.aclose()
