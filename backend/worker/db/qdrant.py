from qdrant_client import AsyncQdrantClient


def create_qdrant(url: str) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=url)
