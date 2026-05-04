from __future__ import annotations

from collections.abc import Sequence

from qdrant_client import AsyncQdrantClient, models

from worker.schemas.document import EmbeddedChunkForIndex
from worker.schemas.document_type import AccessScope, GeoScope


class VectorRepository:
    _client: AsyncQdrantClient
    _collection_name: str
    _upsert_batch_size: int

    def __init__(
        self,
        client: AsyncQdrantClient,
        collection_name: str,
        upsert_batch_size: int = 512,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._upsert_batch_size = upsert_batch_size

    async def upsert_chunks(
        self,
        embedded_chunks: Sequence[EmbeddedChunkForIndex],
        regions: list[str],
        access_scope: AccessScope,
        geo_scope: GeoScope,
        place_of_work: str | None = None,
    ) -> int:
        if not embedded_chunks:
            return 0

        points: list[models.PointStruct] = []

        for chunk in embedded_chunks:
            if not chunk.vector:
                continue

            vector: dict[str, models.Vector] = {
                "chunk": chunk.vector,
            }

            question_vectors = [
                question.vector for question in chunk.questions if question.vector
            ]

            if question_vectors:
                vector["questions"] = question_vectors

            payload = {
                "chunk_id": chunk.id,
                "source_id": chunk.source_id,
                "source_url": chunk.source_url,
                "source_name": chunk.source_name,
                "region_codes": regions,
                "place_of_work": place_of_work,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "geo_scope": geo_scope,
                "access_scope": access_scope,
                "has_questions": bool(question_vectors),
            }

            points.append(
                models.PointStruct(
                    id=chunk.id,
                    vector=vector,
                    payload=payload,
                )
            )

        await self._upsert_points(
            collection_name=self._collection_name,
            points=points,
        )

        return len(points)

    async def delete_chunks_by_source_id(self, source_id: int) -> None:
        await self._delete_by_filter(
            collection_name=self._collection_name,
            key="source_id",
            value=source_id,
        )

    async def delete_chunk_by_chunk_id(self, chunk_id: int) -> None:
        await self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.PointIdsList(
                points=[chunk_id],
            ),
            wait=True,
        )

    async def _delete_by_filter(
        self,
        *,
        collection_name: str,
        key: str,
        value: int | str,
    ) -> None:
        await self._client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        )
                    ]
                )
            ),
            wait=True,
        )

    async def _upsert_points(
        self,
        collection_name: str,
        points: Sequence[models.PointStruct],
    ) -> None:
        if not points:
            return

        for i in range(0, len(points), self._upsert_batch_size):
            batch = points[i : i + self._upsert_batch_size]

            await self._client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True,
            )
