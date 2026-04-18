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
        place_of_work: str | None,
    ) -> list[int]:
        if place_of_work:
            response = await self._client.query_points(
                collection_name=self._config.qdrant_collection,
                prefetch=[
                    models.Prefetch(
                        query=embedding,
                        filter=models.Filter(
                            must=[
                                models.IsNullCondition(
                                    is_null=models.PayloadField(key="place_of_work")
                                )
                            ]
                        ),
                        limit=self._config.rag_top_k,
                        score_threshold=self._config.rag_score_threshold,
                    ),
                    models.Prefetch(
                        query=embedding,
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="place_of_work",
                                    match=models.MatchValue(value=place_of_work),
                                )
                            ]
                        ),
                        limit=self._config.rag_top_k,
                        score_threshold=self._config.rag_score_threshold,
                    ),
                ],
                query=models.RrfQuery(rrf=models.Rrf(weights=[1.0, 2.0])),
                limit=self._config.rag_top_k,
            )
        else:
            response = await self._client.query_points(
                collection_name=self._config.qdrant_collection,
                query=embedding,
                query_filter=models.Filter(
                    must=[
                        models.IsNullCondition(
                            is_null=models.PayloadField(key="place_of_work")
                        )
                    ]
                ),
                limit=self._config.rag_top_k,
                score_threshold=self._config.rag_score_threshold,
            )

        return [point.payload["text_id"] for point in response.points if point.payload]
