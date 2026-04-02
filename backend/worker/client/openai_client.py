from openai import OpenAI, DefaultHttpxClient

from worker.core.config import Config


def build_openai_client(config: Config, timeout: int = 60) -> OpenAI:

    http_client = DefaultHttpxClient(
        verify=False,
        timeout=timeout,
    )
    return OpenAI(
        api_key=config.polza_ai_api_key,
        base_url=config.polza_ai_base_url,
        http_client=http_client,
        max_retries=2,
    )
