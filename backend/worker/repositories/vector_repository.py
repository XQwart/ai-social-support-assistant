from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from qdrant_client import QdrantClient, models
from worker.schemas.document import EmbeddedDocumentChunk


class VectorRepository:
    _client: QdrantClient
    _collection_name: str

    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        self._client = client
        self._collection_name = collection_name

    def upsert_chunks(
        self,
        embedded_chunks: Sequence[EmbeddedDocumentChunk],
        regions: list[str],
        place_of_work: str | None = None,
    ) -> int:
        if not embedded_chunks:
            return 0

        points: list[models.PointStruct] = []
        total_chunks = len(embedded_chunks)
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

        self._client.upsert(
            collection_name=self._collection_name,
            points=points,
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
