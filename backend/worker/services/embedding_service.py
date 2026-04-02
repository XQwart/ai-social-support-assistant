from openai import OpenAI

from worker.schemas.document import StoredDocumentChunk, EmbeddedDocumentChunk


class EmbeddingService:
    _client: OpenAI
    _model: str

    def __init__(self, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def create_embeddings(
        self,
        chunks: list[StoredDocumentChunk],
        access_level: str = "all",
    ) -> list[EmbeddedDocumentChunk]:
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]

        response = self._client.embeddings.create(
            model=self._model,
            input=texts,
            encoding_format="float",
        )
        vectors = [item.embedding for item in response.data]

        return [
            EmbeddedDocumentChunk(
                **chunk.model_dump(),
                vector=vector,
                access_level=access_level,
            )
            for chunk, vector in zip(chunks, vectors)
        ]
