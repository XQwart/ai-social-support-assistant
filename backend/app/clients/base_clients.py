from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(slots=True)
class LLMUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(slots=True)
class LLMCompletion:
    text: str | None
    usage: LLMUsage | None = None


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
    ) -> LLMCompletion:
        pass


class EmbeddingClient(Client):
    @abstractmethod
    async def get_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        pass
