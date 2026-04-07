from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from .base_clients import LLMClient, EmbeddingClient

if TYPE_CHECKING:
    from app.core.config import Config


class _GigaChatMixin:
    _client: GigaChat

    def __init__(self, config: Config, model_name: str | None) -> None:
        self._client = GigaChat(
            credentials=config.gigachat_api_key,
            ca_bundle_file=config.rus_root_ca_cert_path,
            scope=config.gigachat_scope,
            timeout=config.llm_timeout,
            model=model_name,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class GigaChatLLMClient(_GigaChatMixin, LLMClient):
    async def get_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str | None:
        prepared_messages = [
            Messages(role=MessagesRole(msg["role"]), content=msg["content"])
            for msg in messages
        ]

        response = await self._client.achat(
            Chat(
                messages=prepared_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        print(f"Использованная для запроса модель: {response.model}")

        return response.choices[0].message.content


class GigaChatEmbeddingClient(_GigaChatMixin, EmbeddingClient):
    async def get_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = await self._client.aembeddings(texts)
        print(f"Использованная для эмбеддингов модель: {embeddings.model}")

        return [item.embedding for item in embeddings.data]
