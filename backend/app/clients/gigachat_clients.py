from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole, ChatCompletion

from .base_clients import LLMClient, EmbeddingClient, LLMCompletion, LLMUsage

if TYPE_CHECKING:
    from app.core.config import Config


class _GigaChatMixin:
    _client: GigaChat
    _model_name: str | None

    def __init__(self, config: Config, model_name: str | None) -> None:
        self._model_name = model_name
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
    ) -> LLMCompletion:
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

        return LLMCompletion(
            text=response.choices[0].message.content,
            usage=self._extract_usage(response),
        )

    def _extract_usage(self, competetion: ChatCompletion) -> LLMUsage:
        usage = competetion.usage

        return LLMUsage(
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )


class GigaChatEmbeddingClient(_GigaChatMixin, EmbeddingClient):
    _model_name: str

    def __init__(self, config: Config, model_name: str | None) -> None:
        super().__init__(config, model_name)
        self._model_name = model_name if model_name else "Embeddings"

    async def get_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = await self._client.aembeddings(texts, model=self._model_name)

        return [item.embedding for item in embeddings.data]

    async def count_tokens(self, text: str) -> int:
        return len(text) // 2
