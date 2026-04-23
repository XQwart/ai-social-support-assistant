from __future__ import annotations
from abc import ABC, abstractmethod


class Client(ABC):
    @abstractmethod
    async def aclose(self) -> None:
        pass


class LLMClient(Client):
    @abstractmethod
    async def get_completion_text(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        raise NotImplementedError
