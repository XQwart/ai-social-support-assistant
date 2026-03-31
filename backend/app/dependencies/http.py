from typing import Annotated

from fastapi import Request, Depends
import httpx


def get_sber_client(req: Request) -> httpx.AsyncClient:
    return req.app.state.sber_client


HTTPSberClientDep = Annotated[httpx.AsyncClient, Depends(get_sber_client)]
