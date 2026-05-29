from typing import Annotated

from fastapi import Request, Depends
import httpx


def get_sber_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.sber_client

def get_web_search_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.web_search_client

def get_fetch_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.fetch_client


HTTPSberClientDep = Annotated[httpx.AsyncClient, Depends(get_sber_client)]
HTTPWebSearchClientDep = Annotated[httpx.AsyncClient, Depends(get_web_search_client)]
HTTPFetchClientDep = Annotated[httpx.AsyncClient, Depends(get_fetch_client)]