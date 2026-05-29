from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator

from worker.schemas.document import (
    ChunkWithQuestions,
    EmbeddedChunkForIndex,
    EmbeddedChunkQuestion,
)
from worker.services.embedding.base_provider import BaseEmbeddingProvider


class EmbeddingService:
    _provider: BaseEmbeddingProvider
    _batch_size: int

    def __init__(
        self,
        provider: BaseEmbeddingProvider,
        batch_size: int = 256,
    ) -> None:
        self._provider = provider
        self._batch_size = batch_size

    def _iter_batches(self, items: list) -> Iterator[list]:
        for i in range(0, len(items), self._batch_size):
            yield items[i : i + self._batch_size]

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

    async def create_chunk_index_embeddings(
        self,
        chunks: list[ChunkWithQuestions],
    ) -> list[EmbeddedChunkForIndex]:
        if not chunks:
            return []

        chunk_vectors = await self.embed_texts([chunk.text for chunk in chunks])

        flat_questions: list[tuple[int, str]] = []

        for chunk_index, chunk in enumerate(chunks):
            for question_text in chunk.questions:
                flat_questions.append((chunk_index, question_text))

        question_vectors = await self.embed_texts(
            [question_text for _, question_text in flat_questions]
        )

        questions_by_chunk_index: dict[int, list[EmbeddedChunkQuestion]] = defaultdict(
            list
        )

        for (chunk_index, question_text), vector in zip(
            flat_questions,
            question_vectors,
            strict=True,
        ):
            questions_by_chunk_index[chunk_index].append(
                EmbeddedChunkQuestion(
                    vector=vector,
                )
            )

        embedded_chunks: list[EmbeddedChunkForIndex] = []

        for index, (chunk, chunk_vector) in enumerate(
            zip(chunks, chunk_vectors, strict=True)
        ):
            embedded_chunks.append(
                EmbeddedChunkForIndex(
                    **chunk.model_dump(exclude={"questions"}),
                    vector=chunk_vector,
                    questions=questions_by_chunk_index.get(index, []),
                )
            )

        return embedded_chunks

    async def aclose(self) -> None:
        await self._provider.aclose()
