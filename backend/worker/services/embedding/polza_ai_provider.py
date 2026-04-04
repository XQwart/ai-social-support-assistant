from __future__ import annotations

from collections.abc import Sequence

from openai import OpenAI
from worker.services.embedding.base_provider import BaseEmbeddingProvider


class PolzaAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(
        self,
        client: OpenAI,
        model: str,
        vector_size: int,
    ) -> None:
        self._client = client
        self._model = model
        self._vector_size = vector_size

    @property
    def vector_size(self) -> int:
        return self._vector_size

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.embeddings.create(
            model=self._model,
            input=list(texts),
        )

        return [item.embedding for item in response.data]

    def close(self):
        self._client.close()
