from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance


def create_qdrant_client(url: str) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=url)


async def ensure_collection(
    qdrant: AsyncQdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
) -> None:
    if not await qdrant.collection_exists(collection_name):
        await qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance,
            ),
        )
