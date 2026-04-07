from typing import Annotated

from fastapi import Request, Depends

from app.clients import LLMClient, EmbeddingClient


def get_chat_ai_client(request: Request) -> LLMClient:
    return request.app.state.chat_ai_client


def get_compress_ai_client(request: Request) -> LLMClient:
    return request.app.state.compress_ai_client


def get_embedding_ai_client(request: Request) -> EmbeddingClient:
    return request.app.state.embedding_ai_client


ChatAIClientDep = Annotated[LLMClient, Depends(get_chat_ai_client)]
CompressAIClientDep = Annotated[LLMClient, Depends(get_compress_ai_client)]
EmbeddingAIClientDep = Annotated[LLMClient, Depends(get_embedding_ai_client)]
