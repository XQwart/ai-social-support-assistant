from __future__ import annotations
from typing import TYPE_CHECKING

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance

if TYPE_CHECKING:
    from app.core.config import Config


def create_qdrant_client(config: Config) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=config.qdrant_url, port=config.qdrant_port)


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
