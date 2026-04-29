from __future__ import annotations

from collections.abc import Sequence

from gigachat import GigaChat

from worker.services.embedding.base_provider import BaseEmbeddingProvider


class GigaChatEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, client: GigaChat, vector_size: int, model: str) -> None:
        self._client = client
        self._vector_size = vector_size
        self._model = model

    @property
    def vector_size(self) -> int:
        return self._vector_size

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self._client.aembeddings(list(texts), model=self._model)
        return [item.embedding for item in response.data]

    async def aclose(self) -> None:
        await self._client.aclose()
