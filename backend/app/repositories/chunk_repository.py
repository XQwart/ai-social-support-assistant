from __future__ import annotations
from typing import TYPE_CHECKING

from qdrant_client import AsyncQdrantClient

if TYPE_CHECKING:
    from app.core.config import Config


class ChunkRepository:
    _client: AsyncQdrantClient
    _config: Config

    def __init__(self, client: AsyncQdrantClient, config: Config) -> None:
        self._client = client
        self._config = config

    async def search_similar(
        self,
        embedding: list[float],
        top_k: int = 3,
        score_threshold: float = 0.7,
    ) -> list[int]:
        response = await self._client.query_points(
            collection_name=self._config.qdrant_collection,
            query=embedding,
            limit=top_k,
            score_threshold=score_threshold,
        )

        return [point.payload["text_id"] for point in response.points]
