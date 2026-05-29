from __future__ import annotations
import asyncio
import httpx
import random
from gigachat.models import Chat, Messages, MessagesRole
from gigachat import GigaChat

from worker.client.base_clients import LLMClient
from worker.core.config import Config


class GigaChatLLMClient(LLMClient):
    def __init__(self, config: Config, model_name: str | None) -> None:
        self._model_name = model_name
        self._max_retries = 2
        self._retry_base_delay = 1.5
        self._client = GigaChat(
            credentials=config.gigachat_api_key,
            ca_bundle_file=config.rus_root_ca_cert_path,
            scope=config.gigachat_scope,
            timeout=config.llm_timeout,
            model=model_name,
        )

    async def get_completion_text(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        prepared_messages = [
            Messages(
                role=MessagesRole(message["role"]),
                content=message["content"],
            )
            for message in messages
        ]

        chat = Chat(
            messages=prepared_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.achat(chat)
                return response.choices[0].message.content or ""

            except Exception as error:
                last_error = error

                if not self._is_retryable_error(error):
                    raise

                if attempt >= self._max_retries:
                    break

                delay = self._get_retry_delay(attempt)

                await asyncio.sleep(delay)

        raise last_error or RuntimeError("GigaChat request failed")

    def _is_retryable_error(
        self,
        error: Exception,
    ) -> bool:
        if isinstance(
            error,
            (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError,
            ),
        ):
            return True

        status_code = getattr(error, "status_code", None)

        if status_code in {429, 500, 502, 503, 504}:
            return True

        return False

    def _get_retry_delay(
        self,
        attempt: int,
    ) -> float:
        jitter = random.uniform(0, 0.5)
        return self._retry_base_delay * attempt + jitter

    async def aclose(self) -> None:
        await self._client.aclose()
