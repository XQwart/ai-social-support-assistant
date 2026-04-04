from __future__ import annotations
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from .llm_service_base import LLMServiceBase

if TYPE_CHECKING:
    from app.core.config import Config


class PolzaAIService(LLMServiceBase[dict[str, str]]):
    _config: Config
    _client: AsyncOpenAI

    def __init__(self, config: Config):
        super().__init__(config)
        self._client = AsyncOpenAI(
            base_url=config.polza_ai_base_url,
            api_key=config.polza_ai_api_key,
            timeout=config.llm_timeout,
        )

    def _prepare_message(self, message: dict[str, str]) -> dict[str, str]:
        return message

    async def _get_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str | None:
        response = await self._client.chat.completions.create(
            model=self._config.polza_ai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    async def aclose(self) -> None:
        await self._client.close()
