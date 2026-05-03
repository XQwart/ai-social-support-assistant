# app/core/qdrant.py
from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    MultiVectorComparator,
    MultiVectorConfig,
    VectorParams,
)


def create_qdrant_client(url: str) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=url)


async def ensure_collections(
    client: AsyncQdrantClient,
    collection_name: str,
    vector_size: int,
) -> None:
    if await client.collection_exists(collection_name):
        return

    await client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "chunk": VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
            "questions": VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
                multivector_config=MultiVectorConfig(
                    comparator=MultiVectorComparator.MAX_SIM,
                ),
            ),
        },
    )
