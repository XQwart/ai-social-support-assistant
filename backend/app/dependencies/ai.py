from typing import Annotated

from fastapi import Request, Depends
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings.embeddings import Embeddings


def get_chat_ai_client(request: Request) -> BaseChatModel:
    return request.app.state.chat_llm_client


def get_compress_ai_client(request: Request) -> BaseChatModel:
    return request.app.state.compress_llm_client


def get_embedding_ai_client(request: Request) -> Embeddings:
    return request.app.state.embedding_client


ChatLLMClientDep = Annotated[BaseChatModel, Depends(get_chat_ai_client)]
CompressLLMClientDep = Annotated[BaseChatModel, Depends(get_compress_ai_client)]
EmbeddingClientDep = Annotated[Embeddings, Depends(get_embedding_ai_client)]
