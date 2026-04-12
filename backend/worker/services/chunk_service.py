from __future__ import annotations

import logging
import re

import tiktoken

from worker.schemas.document import DocumentChunkCreate, ParsedDocument
from worker.core.constants import _ABBR_SET, _SENTENCE_SPLIT_RE

logger = logging.getLogger(__name__)


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:

        self._chunk_size = chunk_size
        self._overlap = overlap

        try:
            self._encoding = tiktoken.encoding_for_model(embedding_model)
        except KeyError:
            logger.warning(
                "Токенизатор для модели '%s' не найден, используем cl100k_base",
                embedding_model,
            )
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def split_document(self, document: ParsedDocument) -> list[DocumentChunkCreate]:
        chunks = self._split_text(document.text)

        logger.info(
            "Документ '%s' (source_id=%s): %d символов → %d чанков",
            document.source_name,
            document.source_id,
            len(document.text),
            len(chunks),
        )

        return [
            DocumentChunkCreate(
                source_id=document.source_id,
                source_url=document.source_url,
                source_name=document.source_name,
                chunk_index=index,
                text=chunk_text,
            )
            for index, chunk_text in enumerate(chunks)
        ]

    def _split_text(self, text: str) -> list[str]:
        if not text:
            return []

        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        units: list[str] = []
        for paragraph in paragraphs:
            if self._token_len(paragraph) <= self._chunk_size:
                units.append(paragraph)
            else:
                units.extend(self._split_large_paragraph(paragraph))

        return self._merge_units(units)

    def _token_len(self, text: str) -> int:
        return len(self._encoding.encode(text))

    def _encode(self, text: str) -> list[int]:
        return self._encoding.encode(text)

    def _decode(self, tokens: list[int]) -> str:
        return self._encoding.decode(tokens)

    def _split_large_paragraph(self, paragraph: str) -> list[str]:
        sentences = self._split_sentences(paragraph)

        result: list[str] = []
        current = ""

        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence

            if self._token_len(candidate) <= self._chunk_size:
                current = candidate
                continue

            if current:
                result.append(current)

            if self._token_len(sentence) > self._chunk_size:
                result.extend(self._force_split_by_tokens(sentence))
                current = ""
            else:
                current = sentence

        if current:
            result.append(current)

        return result

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        raw_parts = _SENTENCE_SPLIT_RE.split(text)

        sentences: list[str] = []
        buffer = ""

        for part in raw_parts:
            part = part.strip()
            if not part:
                continue

            buffer = f"{buffer} {part}" if buffer else part

            match = re.search(r"(\w+)\.\s*$", buffer)
            if match and match.group(1).lower() in _ABBR_SET:
                continue

            if re.search(r"\d\.\s*$", buffer):
                continue

            sentences.append(buffer)
            buffer = ""

        if buffer:
            sentences.append(buffer)

        return sentences

    def _force_split_by_tokens(self, text: str) -> list[str]:
        tokens = self._encode(text)
        chunks: list[str] = []

        start = 0
        while start < len(tokens):
            end = min(start + self._chunk_size, len(tokens))
            chunk_text = self._decode(tokens[start:end]).strip()

            if chunk_text:
                chunks.append(chunk_text)

            start += self._chunk_size - self._overlap

        return chunks

    def _merge_units(self, units: list[str]) -> list[str]:
        if not units:
            return []

        chunks: list[str] = []
        current = ""

        for unit in units:
            separator = "\n\n" if current else ""
            candidate = f"{current}{separator}{unit}"

            if self._token_len(candidate) <= self._chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current.strip())

                overlap_text = self._extract_overlap(current)
                current = f"{overlap_text}\n\n{unit}" if overlap_text else unit
            else:
                forced = self._force_split_by_tokens(unit)
                chunks.extend(forced[:-1])
                current = forced[-1] if forced else ""

            while self._token_len(current) > self._chunk_size:
                forced = self._force_split_by_tokens(current)
                chunks.extend(forced[:-1])
                current = forced[-1] if forced else ""

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _extract_overlap(self, text: str) -> str:
        tokens = self._encode(text)

        if len(tokens) <= self._overlap:
            return text

        overlap_tokens = tokens[-self._overlap :]
        overlap_text = self._decode(overlap_tokens).strip()

        first_space = overlap_text.find(" ")
        if first_space > 0:
            overlap_text = overlap_text[first_space:].strip()

        return overlap_text
