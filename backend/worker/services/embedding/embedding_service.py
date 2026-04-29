from __future__ import annotations

from collections.abc import Iterator

from worker.schemas.document import (
    StoredDocumentChunk,
    EmbeddedDocumentChunk,
    GeneratedChunkQuestion,
    EmbeddedChunkQuestion,
)
from worker.services.embedding.base_provider import BaseEmbeddingProvider


class EmbeddingService:
    _provider: BaseEmbeddingProvider
    _model: str
    _batch_size: int

    def __init__(
        self,
        provider: BaseEmbeddingProvider,
        model: str,
        batch_size: int = 512,
    ) -> None:
        self._provider = provider
        self._model = model
        self._batch_size = batch_size

    def _iter_batches(self, items: list) -> Iterator[list]:
        for i in range(0, len(items), self._batch_size):
            yield items[i : i + self._batch_size]

    async def create_embeddings(
        self,
        chunks: list[StoredDocumentChunk],
    ) -> list[EmbeddedDocumentChunk]:
        if not chunks:
            return []

        embedded_chunks: list[EmbeddedDocumentChunk] = []

        for batch in self._iter_batches(chunks):
            texts = [chunk.text for chunk in batch]
            vectors = await self._provider.embed_texts(texts=texts)

            if len(vectors) != len(batch):
                raise ValueError(
                    f"Expected {len(batch)} embeddings, got {len(vectors)}"
                )

            embedded_chunks.extend(
                EmbeddedDocumentChunk(
                    **chunk.model_dump(),
                    vector=vector,
                )
                for chunk, vector in zip(batch, vectors, strict=True)
            )

        return embedded_chunks

    async def create_question_embeddings(
        self,
        questions: list[GeneratedChunkQuestion],
    ) -> list[EmbeddedChunkQuestion]:
        if not questions:
            return []

        embedded_questions: list[EmbeddedChunkQuestion] = []

        for batch in self._iter_batches(questions):
            texts = [question.text for question in batch]
            vectors = await self._provider.embed_texts(texts=texts)

            if len(vectors) != len(batch):
                raise ValueError(
                    f"Expected {len(batch)} embeddings, got {len(vectors)}"
                )

            embedded_questions.extend(
                EmbeddedChunkQuestion(
                    **question.model_dump(),
                    vector=vector,
                )
                for question, vector in zip(batch, vectors, strict=True)
            )

        return embedded_questions

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        vectors: list[list[float]] = []

        for batch in self._iter_batches(texts):
            batch_vectors = await self._provider.embed_texts(texts=batch)

            if len(batch_vectors) != len(batch):
                raise ValueError(
                    f"Expected {len(batch)} embeddings, got {len(batch_vectors)}"
                )

            vectors.extend(batch_vectors)

        return vectors

    async def aclose(self) -> None:
        await self._provider.aclose()
