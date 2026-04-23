from openai import AsyncOpenAI

from worker.core.config import Config


def build_polza_ai_client(config: Config, timeout: int = 60) -> AsyncOpenAI:

    return AsyncOpenAI(
        api_key=config.polza_ai_api_key,
        base_url=config.polza_ai_base_url,
        timeout=timeout,
        max_retries=2,
    )
