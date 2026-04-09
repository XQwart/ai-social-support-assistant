from typing import Annotated

from fastapi import Depends, Request
from qdrant_client import AsyncQdrantClient


def get_qdrant(request: Request) -> AsyncQdrantClient:
    return request.app.state.qdrant


QdrantClientDep = Annotated[AsyncQdrantClient, Depends(get_qdrant)]
