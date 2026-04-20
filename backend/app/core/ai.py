from __future__ import annotations
from typing import TYPE_CHECKING

from app.clients import (
    EmbeddingClient,
    LLMClient,
    GigaChatEmbeddingClient,
    GigaChatLLMClient,
    PolzaEmbeddingClient,
    PolzaLLMClient,
)
from .config import AIProvider

if TYPE_CHECKING:
    from .config import Config


def create_ai_clients(config: Config) -> tuple[LLMClient, LLMClient, EmbeddingClient]:
    match config.ai_provider:
        case AIProvider.POLZA:
            chat_client = PolzaLLMClient(config, model_name=config.polza_ai_model)
            compress_client = (
                PolzaLLMClient(config, model_name=config.polza_ai_compress_model)
                if config.polza_ai_compress_model
                else chat_client
            )
            embedding_client = PolzaEmbeddingClient(
                config,
                model_name=config.polza_ai_embedding_model,
                vector_size=config.polza_ai_embedding_vector_size,
            )

            return chat_client, compress_client, embedding_client
        case AIProvider.GIGACHAT:
            chat_client = GigaChatLLMClient(config, model_name=config.gigachat_model)
            compress_client = (
                GigaChatLLMClient(config, model_name=config.gigachat_compress_model)
                if config.gigachat_compress_model
                else chat_client
            )
            embedding_client = GigaChatEmbeddingClient(
                config,
                model_name=config.gigachat_embedding_model,
                vector_size=config.gigachat_embedding_vector_size,
            )

            return chat_client, compress_client, embedding_client
