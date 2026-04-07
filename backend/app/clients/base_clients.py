from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence


class Client(ABC):
    @abstractmethod
    async def aclose(self) -> None:
        pass


class LLMClient(Client):
    @abstractmethod
    async def get_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str | None:
        pass


class EmbeddingClient(Client):
    @abstractmethod
    async def get_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        pass
