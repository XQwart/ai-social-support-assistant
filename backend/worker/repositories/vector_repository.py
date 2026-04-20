from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from qdrant_client import QdrantClient, models
from worker.schemas.document import EmbeddedDocumentChunk


class VectorRepository:
    _client: QdrantClient
    _collection_name: str
    _upsert_batch_size: int

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        upsert_batch_size: int = 512,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._upsert_batch_size = upsert_batch_size

    def upsert_chunks(
        self,
        embedded_chunks: Sequence[EmbeddedDocumentChunk],
        regions: list[str],
        place_of_work: str | None = None,
    ) -> int:
        if not embedded_chunks:
            return 0

        total_chunks = len(embedded_chunks)
        points: list[models.PointStruct] = []

        for chunk in embedded_chunks:
            vector = chunk.vector
            if not vector:
                continue

            payload = {
                "text_id": chunk.id,
                "source_id": chunk.source_id,
                "region_codes": regions,
                "place_of_work": place_of_work,
                "chunk_index": chunk.chunk_index,
                "total_chunks": total_chunks,
            }

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload,
                )
            )

        if not points:
            return 0

        for i in range(0, len(points), self._upsert_batch_size):
            batch = points[i : i + self._upsert_batch_size]
            self._client.upsert(
                collection_name=self._collection_name,
                points=batch,
            )

        return len(points)

    def delete_by_source_id(self, source_id: int) -> None:
        self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="source_id",
                            match=models.MatchValue(value=source_id),
                        )
                    ]
                )
            ),
        )
