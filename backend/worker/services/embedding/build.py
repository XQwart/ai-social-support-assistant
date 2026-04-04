from __future__ import annotations

from worker.client.gigachat_client import build_gigachat_client
from worker.client.polza_ai_client import build_polza_ai_client
from worker.core.config import Config
from worker.services.embedding.gigachat_provider import GigaChatEmbeddingProvider
from worker.services.embedding.polza_ai_provider import PolzaAIEmbeddingProvider
from worker.core.config import LLMProvider


def build_embedding_provider(config: Config):
    match config.embedding_provider:
        case LLMProvider.GIGACHAT:
            client = build_gigachat_client(config)
            return GigaChatEmbeddingProvider(
                client=client,
                vector_size=config.gigachat_vector_size,
                model=config.gigachat_embedding_model,
            )

        case LLMProvider.POLZA:
            client = build_polza_ai_client(config)
            return PolzaAIEmbeddingProvider(
                client=client,
                model=config.polza_ai_embedding_model,
                vector_size=config.polza_ai_vector_size,
            )

    raise ValueError(f"Unsupported embedding provider: {config.embedding_provider}")
