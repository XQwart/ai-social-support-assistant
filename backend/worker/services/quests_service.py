from __future__ import annotations

import asyncio
import json
import logging
import re
from worker.core.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from worker.client.base_clients import LLMClient
from worker.schemas.document import StoredDocumentChunk, ChunkWithQuestions

logger = logging.getLogger(__name__)


class ChunkQuestionLLMService:
    def __init__(
        self,
        llm_client: LLMClient,
        questions_per_chunk: int = 3,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        concurrency: int = 5,
    ) -> None:

        self._llm_client = llm_client
        self._questions_per_chunk = questions_per_chunk
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._concurrency = concurrency

    async def generate_for_chunk(
        self,
        chunk: StoredDocumentChunk,
    ) -> ChunkWithQuestions:
        messages = self._build_messages(chunk.text)

        raw_text = await self._llm_client.get_completion_text(
            messages=messages,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        questions_text = self._parse_questions(raw_text)

        if not questions_text:
            return ChunkWithQuestions(
                **chunk.model_dump(),
                questions=[],
            )

        logger.info(questions_text)

        return ChunkWithQuestions(**chunk.model_dump(), questions=questions_text)

    async def generate_for_chunks(
        self,
        chunks: list[StoredDocumentChunk],
    ) -> list[ChunkWithQuestions]:
        if not chunks:
            return []

        semaphore = asyncio.Semaphore(self._concurrency)

        async def _wrapped(
            chunk: StoredDocumentChunk,
        ) -> ChunkWithQuestions:
            async with semaphore:
                try:
                    return await self.generate_for_chunk(chunk)
                except Exception:
                    logger.exception(
                        "Ошибка генерации вопросов для chunk_id=%s",
                        chunk.id,
                    )
                    return ChunkWithQuestions(
                        **chunk.model_dump(),
                        questions=[],
                    )

        results = await asyncio.gather(*(_wrapped(chunk) for chunk in chunks))
        return results

    def _build_messages(self, chunk_text: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    questions_per_chunk=self._questions_per_chunk,
                    chunk_text=chunk_text,
                ),
            },
        ]

    def _parse_questions(self, raw_text: str) -> list[str]:
        raw_text = raw_text.strip()
        if not raw_text:
            return []

        parsed = self._try_parse_json(raw_text)
        if parsed is None:
            parsed = self._fallback_parse_lines(raw_text)

        result: list[str] = []
        seen: set[str] = set()
        invalid_values = {
            "",
            "[]",
            "[ ]",
            "null",
            "none",
            "нет вопросов",
            "нет подходящих вопросов",
            "no questions",
        }

        for item in parsed:
            cleaned = " ".join(item.split()).strip()
            normalized = cleaned.casefold()

            if normalized in invalid_values:
                continue

            if not cleaned:
                continue

            key = cleaned.casefold()
            if key in seen:
                continue

            seen.add(key)
            result.append(cleaned)

        return result

    def _try_parse_json(self, raw_text: str) -> list[str] | None:
        match = re.search(r"\[[\s\S]*\]", raw_text)
        json_text = match.group(0) if match else raw_text

        try:
            data = json.loads(json_text)
        except Exception:
            return None

        if not isinstance(data, list):
            return None

        return [item for item in data if isinstance(item, str)]

    def _fallback_parse_lines(self, raw_text: str) -> list[str]:
        result: list[str] = []

        for line in raw_text.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue

            cleaned = re.sub(r"^\d+[\).\s-]+", "", cleaned)
            cleaned = re.sub(r"^[-*•]\s*", "", cleaned).strip()

            if cleaned:
                result.append(cleaned)

        return result
