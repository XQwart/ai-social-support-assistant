from qdrant_client import QdrantClient


def create_qdrant(url: str) -> QdrantClient:
    return QdrantClient(url=url)
