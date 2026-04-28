from __future__ import annotations
from typing import TYPE_CHECKING

from qdrant_client import AsyncQdrantClient, models

if TYPE_CHECKING:
    from app.core.config import Config


class ChunkRepository:
    _client: AsyncQdrantClient
    _config: Config

    def __init__(self, client: AsyncQdrantClient, config: Config) -> None:
        self._client = client
        self._config = config

    async def search_similar_by_work(
        self,
        embedding: list[float],
        region: str | None,
        place_of_work: str | None,
    ) -> list[tuple[int, str | None]]:

        per_category_k = self._config.rag_min_per_category
        threshold = self._config.rag_score_threshold

        prefetches = [
            models.Prefetch(
                query=embedding,
                filter=models.Filter(
                    must=[
                        models.IsNullCondition(
                            is_null=models.PayloadField(key="region_codes")
                        ),
                        models.IsNullCondition(
                            is_null=models.PayloadField(key="place_of_work")
                        ),
                    ]
                ),
                limit=per_category_k,
                score_threshold=threshold,
            )
        ]

        if region:
            prefetches.append(
                models.Prefetch(
                    query=embedding,
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="region_codes",
                                match=models.MatchAny(any=[region]),
                            ),
                        ]
                    ),
                    limit=per_category_k,
                    score_threshold=threshold,
                )
            )

        if place_of_work:
            prefetches.append(
                models.Prefetch(
                    query=embedding,
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="place_of_work",
                                match=models.MatchValue(value=place_of_work),
                            ),
                        ]
                    ),
                    limit=per_category_k,
                    score_threshold=threshold,
                )
            )

        response = await self._client.query_points(
            collection_name=self._config.qdrant_collection,
            prefetch=prefetches,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=self._config.rag_top_k,
        )

        return [
            (point.payload["text_id"], point.payload.get("place_of_work"))
            for point in response.points
            if point.payload
        ]
