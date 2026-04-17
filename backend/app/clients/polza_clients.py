from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from openai import AsyncOpenAI

from .base_clients import LLMClient, EmbeddingClient, LLMCompletion

if TYPE_CHECKING:
    from app.core.config import Config


class _PolzaMixin:
    _client: AsyncOpenAI
    _model_name: str

    def __init__(self, config: Config, model_name: str, *args) -> None:
        self._model_name = model_name
        self._client = AsyncOpenAI(
            base_url=config.polza_ai_base_url,
            api_key=config.polza_ai_api_key,
            timeout=config.llm_timeout,
        )
        super().__init__(*args)

    async def aclose(self) -> None:
        await self._client.close()


class PolzaLLMClient(_PolzaMixin, LLMClient):
    async def get_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> LLMCompletion:
        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMCompletion(text=response.choices[0].message.content)


class PolzaEmbeddingClient(_PolzaMixin, EmbeddingClient):
    def __init__(self, config: Config, model_name: str, vector_size: int) -> None:
        super().__init__(config, model_name, vector_size)

    async def get_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        return await super().get_embeddings(texts)

    async def count_tokens(self, text: str) -> int:
        return await super().count_tokens(text)
