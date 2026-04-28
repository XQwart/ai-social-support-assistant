from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from qdrant_client import AsyncQdrantClient, models

from worker.schemas.document import EmbeddedDocumentChunk, EmbeddedChunkQuestion


class VectorRepository:
    _client: AsyncQdrantClient
    _chunks_collection_name: str
    _questions_collection_name: str
    _upsert_batch_size: int

    def __init__(
        self,
        client: AsyncQdrantClient,
        chunks_collection_name: str,
        questions_collection_name: str,
        upsert_batch_size: int = 512,
    ) -> None:
        self._client = client
        self._chunks_collection_name = chunks_collection_name
        self._questions_collection_name = questions_collection_name
        self._upsert_batch_size = upsert_batch_size

    async def upsert_chunks(
        self,
        embedded_chunks: Sequence[EmbeddedDocumentChunk],
        regions: list[str],
        place_of_work: str | None = None,
    ) -> int:
        if not embedded_chunks:
            return 0

        total_chunks = len(embedded_chunks)
        points: list[models.PointStruct] = []
        chunk_id_to_point_id: dict[int, str] = {}

        for chunk in embedded_chunks:
            if not chunk.vector:
                continue

            point_id = str(uuid4())
            chunk_id_to_point_id[chunk.id] = point_id

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
                    vector=chunk.vector,
                    payload=payload,
                )
            )

        await self._upsert_points(
            collection_name=self._chunks_collection_name,
            points=points,
        )
        return len(points)

    async def upsert_questions(
        self,
        embedded_questions: Sequence[EmbeddedChunkQuestion],
        regions: list[str],
        place_of_work: str | None = None,
    ) -> int:
        if not embedded_questions:
            return 0

        points: list[models.PointStruct] = []

        for question in embedded_questions:
            if not question.vector:
                continue

            payload = {
                "chunk_id": question.chunk_id,
                "source_id": question.source_id,
                "region_codes": regions,
                "place_of_work": place_of_work,
                "chunk_index": question.chunk_index,
                "question_text": question.text,
            }

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=question.vector,
                    payload=payload,
                )
            )

        await self._upsert_points(
            collection_name=self._questions_collection_name,
            points=points,
        )
        return len(points)

    async def delete_chunks_by_source_id(self, source_id: int) -> None:
        await self._delete_by_source_id(
            collection_name=self._chunks_collection_name,
            source_id=source_id,
        )

    async def delete_questions_by_source_id(self, source_id: int) -> None:
        await self._delete_by_source_id(
            collection_name=self._questions_collection_name,
            source_id=source_id,
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
            )

    async def _delete_by_source_id(
        self,
        collection_name: str,
        source_id: int,
    ) -> None:
        await self._client.delete(
            collection_name=collection_name,
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
