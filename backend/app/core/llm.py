from __future__ import annotations
from typing import TYPE_CHECKING

from app.services.llm import LLMServiceBase, GigaChatService, PolzaAIService

from .config import LLMProvider

if TYPE_CHECKING:
    from .config import Config


def create_llm_service(config: Config) -> LLMServiceBase:
    match config.llm_provider:
        case LLMProvider.POLZA:
            return PolzaAIService(config)
        case LLMProvider.GIGACHAT:
            return GigaChatService(config)
