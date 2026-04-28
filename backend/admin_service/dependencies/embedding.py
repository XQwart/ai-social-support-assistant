from __future__ import annotations
from typing import Annotated, TYPE_CHECKING

from fastapi import Depends, Request

if TYPE_CHECKING:
    from langchain_core.embeddings.embeddings import Embeddings


def get_embedding(request: Request) -> "Embeddings":
    return request.app.state.embedding_client


EmbeddingClientDep = Annotated["Embeddings", Depends(get_embedding)]
