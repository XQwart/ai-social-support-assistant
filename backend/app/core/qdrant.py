from __future__ import annotations
from typing import TYPE_CHECKING

from qdrant_client import AsyncQdrantClient

if TYPE_CHECKING:
    from app.core.config import Config


def create_qdrant_client(config: Config) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=config.qdrant_url, port=config.qdrant_port)
