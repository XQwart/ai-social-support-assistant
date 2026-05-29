from __future__ import annotations
from typing import Any, TYPE_CHECKING

from qdrant_client import AsyncQdrantClient, models

from shared.schemas.document_type import AccessScope, GeoScope

if TYPE_CHECKING:
    from app.core.config import Config


def _eq(key: str, value: str) -> models.FieldCondition:
    return models.FieldCondition(key=key, match=models.MatchValue(value=value))


class ChunkRepository:
    _client: AsyncQdrantClient
    _config: Config

    _PUBLIC_SCOPE = _eq("access_scope", AccessScope.PUBLIC)
    _INTERNAL_SCOPE = _eq("access_scope", AccessScope.INTERNAL)

    _REGIONAL_SCOPE = _eq("geo_scope", GeoScope.REGIONAL)
    _FEDERAL_SCOPE = _eq("geo_scope", GeoScope.FEDERAL)

    def __init__(self, client: AsyncQdrantClient, config: Config) -> None:
        self._client = client
        self._config = config

    async def search_relevant_chunks(
        self,
        embedding: list[float],
        region: str | None,
        place_of_work: str | None,
    ) -> list[tuple[int, str | None]]:
        per_category_k = self._config.qdrant_min_per_category
        threshold = self._config.rag_score_threshold

        prefetches = self._build_prefetch_pair(
            embedding=embedding,
            must=[
                self._PUBLIC_SCOPE,
                self._FEDERAL_SCOPE,
            ],
            limit=per_category_k,
            threshold=threshold,
        )

        if region:
            prefetches.extend(
                self._build_prefetch_pair(
                    embedding=embedding,
                    must=[
                        self._PUBLIC_SCOPE,
                        self._REGIONAL_SCOPE,
                        models.FieldCondition(
                            key="region_codes", match=models.MatchAny(any=[region])
                        ),
                    ],
                    limit=per_category_k,
                    threshold=threshold,
                )
            )

        if place_of_work:
            prefetches.extend(
                self._build_prefetch_pair(
                    embedding=embedding,
                    must=[
                        self._INTERNAL_SCOPE,
                        self._FEDERAL_SCOPE,
                        _eq("place_of_work", place_of_work),
                    ],
                    limit=per_category_k,
                    threshold=threshold,
                )
            )

        if place_of_work and region:
            prefetches.extend(
                self._build_prefetch_pair(
                    embedding=embedding,
                    must=[
                        self._INTERNAL_SCOPE,
                        self._REGIONAL_SCOPE,
                        models.FieldCondition(
                            key="region_codes", match=models.MatchAny(any=[region])
                        ),
                        _eq("place_of_work", place_of_work),
                    ],
                    limit=per_category_k,
                    threshold=threshold,
                )
            )

        response = await self._client.query_points(
            collection_name=self._config.qdrant_collection,
            prefetch=prefetches,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=len(prefetches) // 2 * per_category_k,
        )

        return [
            (point.payload["chunk_id"], point.payload.get("place_of_work"))
            for point in response.points
            if point.payload and point.payload.get("chunk_id") is not None
        ]

    def _build_prefetch_pair(
        self,
        embedding: list[float],
        must: list[models.Condition],
        limit: int,
        threshold: float,
    ) -> list[models.Prefetch]:
        flt = models.Filter(must=must) if must else None
        return [
            models.Prefetch(
                query=embedding,
                using=self._config.qdrant_vector_chunk,
                filter=flt,
                limit=limit,
                score_threshold=threshold,
            ),
            models.Prefetch(
                query=embedding,
                using=self._config.qdrant_vector_questions,
                filter=models.Filter(
                    must=[
                        *(must or []),
                        models.FieldCondition(
                            key="has_questions",
                            match=models.MatchValue(value=True),
                        ),
                    ]
                ),
                limit=limit,
            ),
        ]
