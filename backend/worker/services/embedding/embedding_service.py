from collections.abc import Iterator

from worker.schemas.document import StoredDocumentChunk, EmbeddedDocumentChunk
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

    def _iter_batches(
        self,
        chunks: list[StoredDocumentChunk],
    ) -> Iterator[list[StoredDocumentChunk]]:
        for i in range(0, len(chunks), self._batch_size):
            yield chunks[i : i + self._batch_size]

    def create_embeddings(
        self,
        chunks: list[StoredDocumentChunk],
    ) -> list[EmbeddedDocumentChunk]:
        if not chunks:
            return []

        embedded_chunks: list[EmbeddedDocumentChunk] = []

        for batch in self._iter_batches(chunks):
            texts = [chunk.text for chunk in batch]
            vectors = self._provider.embed_texts(texts=texts)

            if len(vectors) != len(batch):
                raise ValueError(
                    f"Expected {len(batch)} embeddings, got {len(vectors)}"
                )

            embedded_chunks.extend(
                EmbeddedDocumentChunk(
                    **chunk.model_dump(),
                    vector=vector,
                )
                for chunk, vector in zip(batch, vectors)
            )

        return embedded_chunks
