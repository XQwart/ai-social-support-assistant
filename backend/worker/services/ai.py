from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from worker.core.prompts import FAQ_EXTRACTION_PROMPT
from openai import OpenAI, DefaultHttpxClient


if TYPE_CHECKING:
    from worker.core.config import Config


logger = logging.getLogger(__name__)


class AIService:
    _config: Config
    _model: str

    def __init__(self, config: Config):
        self._config = config
        self._model = config.polza_ai_model

    def _create_client(self, timeout: float = 60.0) -> OpenAI:

        http_client = DefaultHttpxClient(
            verify=False,
            timeout=timeout,
        )

        return OpenAI(
            base_url=self._config.polza_ai_base_url,
            api_key=self._config.polza_ai_api_key,
            max_retries=2,
            http_client=http_client,
        )

    def extract_faq_from_texts(self, texts: list[dict]) -> list[dict]:
        combined = "\n\n---\n\n".join(
            f"Источник: {t.get('source_url', 'N/A')}\n"
            f"Регион: {t.get('region', 'N/A')}\n"
            f"Текст:\n{t.get('text', '')[:3000]}"
            for t in texts
        )

        try:
            completion = self._create_client(timeout=120.0).chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": FAQ_EXTRACTION_PROMPT},
                    {"role": "user", "content": combined},
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            raw = completion.choices[0].message.content or "[]"
            raw = raw.strip()

            if raw.startswith("```"):
                lines = raw.split("\n", 1)
                raw = lines[1] if len(lines) > 1 else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            result = json.loads(raw)
            return result

        except json.JSONDecodeError as e:
            logger.error(
                "Ошибка декодирования JSON при извлечении FAQ: %s. Raw content: %s",
                e,
                raw[:200],
            )
            return []
        except Exception:
            logger.exception("Непредвиденная ошибка при извлечении FAQ")
            return []
