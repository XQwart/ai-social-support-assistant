from __future__ import annotations

import asyncio
import json
import logging
import re

from worker.client.base_clients import LLMClient
from worker.schemas.document import StoredDocumentChunk, GeneratedChunkQuestion

logger = logging.getLogger(__name__)


class ChunkQuestionLLMService:
    def __init__(
        self,
        llm_client: LLMClient,
        questions_per_chunk: int = 2,
        max_tokens: int = 512,
        temperature: float = 0.1,
        concurrency: int = 10,
    ) -> None:

        self._llm_client = llm_client
        self._questions_per_chunk = questions_per_chunk
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._concurrency = concurrency

    async def generate_for_chunk(
        self,
        chunk: StoredDocumentChunk,
    ) -> list[GeneratedChunkQuestion]:
        messages = self._build_messages(chunk.text)

        raw_text = await self._llm_client.get_completion_text(
            messages=messages,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        logger.info("chunk_id=%s raw_text=%r", chunk.id, raw_text[:1000])
        questions_text = self._parse_questions(raw_text)
        if not questions_text:
            return []

        logger.info(questions_text)
        return [
            GeneratedChunkQuestion(
                chunk_id=chunk.id,
                source_id=chunk.source_id,
                source_url=chunk.source_url,
                source_name=chunk.source_name,
                chunk_index=chunk.chunk_index,
                text=question_text,
            )
            for question_text in questions_text
        ]

    async def generate_for_chunks(
        self,
        chunks: list[StoredDocumentChunk],
    ) -> list[GeneratedChunkQuestion]:
        if not chunks:
            return []

        semaphore = asyncio.Semaphore(self._concurrency)

        async def _wrapped(
            chunk: StoredDocumentChunk,
        ) -> list[GeneratedChunkQuestion]:
            async with semaphore:
                try:
                    return await self.generate_for_chunk(chunk)
                except Exception:
                    logger.exception(
                        "Ошибка генерации вопросов для chunk_id=%s",
                        chunk.id,
                    )
                    return []

        results = await asyncio.gather(*(_wrapped(chunk) for chunk in chunks))
        return [question for batch in results for question in batch]

    def _build_messages(self, chunk_text: str) -> list[dict[str, str]]:

        return [
            {
                "role": "system",
                "content": (
                    "Ты генерируешь поисковые запросы для retrieval-системы. "
                    "Верни только JSON-массив строк без пояснений и без markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Сгенерируй до {self._questions_per_chunk} разных поисковых запросов по тексту.\n"
                    "Каждый запрос должен помогать найти этот фрагмент документа.\n"
                    "Запросы должны быть разными по смыслу, а не просто перефразами.\n"
                    "Старайся покрывать разные интенты, если они есть в тексте: "
                    "кто имеет право, какие условия, какие документы нужны, как оформить, "
                    "какой размер выплаты, какие сроки, кто принимает решение, облагается ли налогом.\n"
                    "Не повторяй один и тот же смысл разными словами.\n"
                    "Не пиши слишком общие запросы без конкретного предмета.\n"
                    "Если в тексте есть только один полезный смысл, верни один запрос.\n"
                    "Если самостоятельных поисковых запросов нет, верни [].\n\n"
                    "Примеры хороших запросов:\n"
                    "- Кто может получить материальную помощь?\n"
                    "- Какие документы нужны для компенсации расходов на ЭКО?\n"
                    "- Как оформить ежемесячное пособие неработающему пенсионеру?\n"
                    "- Облагается ли НДФЛ компенсация медицинских расходов на ребенка?\n\n"
                    "Примеры плохих запросов:\n"
                    "- Какие выплаты предусмотрены?\n"
                    "- Какие документы нужны?\n"
                    "- компенсация документы выплаты\n\n"
                    "Ответ верни только в виде JSON-массива строк.\n\n"
                    f"Текст:\n{chunk_text}"
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

        return result[: self._questions_per_chunk]

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
