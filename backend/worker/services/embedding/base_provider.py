from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class BaseEmbeddingProvider(ABC):
    @property
    @abstractmethod
    def vector_size(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError
