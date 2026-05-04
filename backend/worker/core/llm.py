from __future__ import annotations

from worker.core.config import Config
from worker.services.llm.gigachat_llm_client import GigaChatLLMClient


def build_llm_client(config: Config):

    return GigaChatLLMClient(
        config=config,
        model_name=config.gigachat_quest_model,
    )
