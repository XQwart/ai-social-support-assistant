from __future__ import annotations
from typing import TYPE_CHECKING

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    MultiVectorComparator,
    MultiVectorConfig,
    VectorParams,
)

if TYPE_CHECKING:
    from app.core.config import Config


def create_qdrant_client(config: Config) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=config.qdrant_url, timeout=config.qdrant_timeout)


async def ensure_collection(
    qdrant: AsyncQdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
) -> None:
    if await qdrant.collection_exists(collection_name):
        return

    await qdrant.create_collection(
        collection_name=collection_name,
        vectors_config={
            "chunk": VectorParams(size=vector_size, distance=distance),
            "questions": VectorParams(
                size=vector_size,
                distance=distance,
                multivector_config=MultiVectorConfig(
                    comparator=MultiVectorComparator.MAX_SIM,
                ),
            ),
        },
    )
