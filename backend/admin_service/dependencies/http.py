from __future__ import annotations
from typing import Annotated

import httpx
from fastapi import Depends, Request


def get_chunk_api_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.chunk_api_client


ChunkApiClientDep = Annotated[httpx.AsyncClient, Depends(get_chunk_api_client)]
