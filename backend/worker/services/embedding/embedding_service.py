from worker.schemas.document import StoredDocumentChunk, EmbeddedDocumentChunk
from worker.services.embedding.base_provider import BaseEmbeddingProvider


class EmbeddingService:
    _provider: BaseEmbeddingProvider
    _model: str

    def __init__(self, provider: BaseEmbeddingProvider, model: str) -> None:
        self._provider = provider
        self._model = model

    def create_embeddings(
        self,
        chunks: list[StoredDocumentChunk],
        access_level: str = "all",
    ) -> list[EmbeddedDocumentChunk]:
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]

        vectors = self._provider.embed_texts(texts=texts)

        return [
            EmbeddedDocumentChunk(
                **chunk.model_dump(),
                vector=vector,
                access_level=access_level,
            )
            for chunk, vector in zip(chunks, vectors)
        ]
