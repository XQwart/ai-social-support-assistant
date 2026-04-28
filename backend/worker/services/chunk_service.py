from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from enum import Enum

import tiktoken

from worker.core.constants import ABBR_SET, SENTENCE_SPLIT_RE
from worker.schemas.document import DocumentChunkCreate, ParsedDocument

logger = logging.getLogger(__name__)


class _UnitKind(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    PAGE = "page"
    NOTES = "notes"


@dataclass(frozen=True)
class _ChunkUnit:
    kind: _UnitKind
    text: str


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = 1024,
        overlap: int = 100,
        embedding_model: str = "text-embedding-3-small",
        keep_page_markers: bool = False,
        keep_notes: bool = True,
    ) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._keep_page_markers = keep_page_markers
        self._keep_notes = keep_notes

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

        text = self._prepare_text(text)

        units = self._split_to_units(text)

        split_units: list[_ChunkUnit] = []

        for unit in units:
            if self._token_len(unit.text) <= self._chunk_size:
                split_units.append(unit)
            else:
                split_units.extend(self._split_large_unit(unit))

        chunks = self._merge_units(split_units)

        result: list[str] = []
        seen_hashes: set[str] = set()

        for chunk in chunks:
            chunk = chunk.strip()

            if not chunk:
                continue

            chunk_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()

            if chunk_hash in seen_hashes:
                continue

            seen_hashes.add(chunk_hash)
            result.append(chunk)

        return result

    @staticmethod
    def _prepare_text(text: str) -> str:
        text = text.replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _split_to_units(self, text: str) -> list[_ChunkUnit]:
        units: list[_ChunkUnit] = []

        lines = text.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            if self._is_page_marker(stripped):
                if self._keep_page_markers:
                    units.append(_ChunkUnit(_UnitKind.PAGE, stripped))

                i += 1
                continue

            if self._is_notes_header(stripped):
                note_lines = [stripped]
                i += 1

                while i < len(lines):
                    next_line = lines[i].rstrip()
                    next_stripped = next_line.strip()

                    if not next_stripped:
                        break

                    if self._is_page_marker(next_stripped):
                        break

                    note_lines.append(next_stripped)
                    i += 1

                if self._keep_notes:
                    units.append(
                        _ChunkUnit(
                            _UnitKind.NOTES,
                            "\n".join(note_lines).strip(),
                        )
                    )

                continue

            if self._is_table_title(stripped):
                title = stripped
                i += 1

                while i < len(lines) and not lines[i].strip():
                    i += 1

                if i < len(lines) and self._is_table_line(lines[i].strip()):
                    table_lines = [title]

                    while i < len(lines):
                        next_line = lines[i].rstrip()
                        next_stripped = next_line.strip()

                        if not self._is_table_line(next_stripped):
                            break

                        table_lines.append(next_stripped)
                        i += 1

                    units.append(
                        _ChunkUnit(
                            _UnitKind.TABLE,
                            "\n".join(table_lines).strip(),
                        )
                    )
                    continue

                units.append(_ChunkUnit(_UnitKind.HEADING, title))
                continue

            if self._is_table_line(stripped):
                table_lines: list[str] = []

                while i < len(lines):
                    next_line = lines[i].rstrip()
                    next_stripped = next_line.strip()

                    if not self._is_table_line(next_stripped):
                        break

                    table_lines.append(next_stripped)
                    i += 1

                units.append(
                    _ChunkUnit(
                        _UnitKind.TABLE,
                        "\n".join(table_lines).strip(),
                    )
                )
                continue

            paragraph_lines = [stripped]
            i += 1

            while i < len(lines):
                next_line = lines[i].rstrip()
                next_stripped = next_line.strip()

                if not next_stripped:
                    break

                if self._is_page_marker(next_stripped):
                    break

                if self._is_notes_header(next_stripped):
                    break

                if self._is_table_title(next_stripped):
                    break

                if self._is_table_line(next_stripped):
                    break

                paragraph_lines.append(next_stripped)
                i += 1

            paragraph = "\n".join(paragraph_lines)
            units.extend(self._split_paragraph_to_units(paragraph))

        return [unit for unit in units if unit.text.strip()]

    def _split_paragraph_to_units(self, paragraph: str) -> list[_ChunkUnit]:
        paragraph = self._restore_newlines_inside_block(paragraph)

        result: list[_ChunkUnit] = []

        for raw_block in paragraph.splitlines():
            block = raw_block.strip()

            if not block:
                continue

            kind = _UnitKind.HEADING if self._is_heading(block) else _UnitKind.TEXT
            result.append(_ChunkUnit(kind, block))

        return result

    def _split_large_unit(self, unit: _ChunkUnit) -> list[_ChunkUnit]:
        if unit.kind == _UnitKind.TABLE:
            return self._split_large_table(unit.text)

        return self._split_large_text_unit(unit)

    def _split_large_text_unit(self, unit: _ChunkUnit) -> list[_ChunkUnit]:
        sentences = self._split_sentences(unit.text)

        if not sentences:
            return self._split_by_words(unit.text, unit.kind)

        result: list[_ChunkUnit] = []
        current_parts: list[str] = []

        for sentence in sentences:
            if self._token_len(sentence) > self._chunk_size:
                if current_parts:
                    result.append(
                        _ChunkUnit(
                            unit.kind,
                            " ".join(current_parts).strip(),
                        )
                    )
                    current_parts = []

                result.extend(self._split_by_words(sentence, unit.kind))
                continue

            candidate = (
                " ".join(current_parts + [sentence]).strip()
                if current_parts
                else sentence
            )

            if self._token_len(candidate) <= self._chunk_size:
                current_parts.append(sentence)
            else:
                if current_parts:
                    result.append(
                        _ChunkUnit(
                            unit.kind,
                            " ".join(current_parts).strip(),
                        )
                    )

                current_parts = [sentence]

        if current_parts:
            result.append(
                _ChunkUnit(
                    unit.kind,
                    " ".join(current_parts).strip(),
                )
            )

        return result

    def _split_by_words(self, text: str, kind: _UnitKind) -> list[_ChunkUnit]:
        words = text.split()

        if not words:
            return []

        result: list[_ChunkUnit] = []
        current_words: list[str] = []

        for word in words:
            candidate = (
                " ".join(current_words + [word]).strip() if current_words else word
            )

            if self._token_len(candidate) <= self._chunk_size:
                current_words.append(word)
                continue

            if current_words:
                result.append(
                    _ChunkUnit(
                        kind,
                        " ".join(current_words).strip(),
                    )
                )

            current_words = [word]

        if current_words:
            result.append(
                _ChunkUnit(
                    kind,
                    " ".join(current_words).strip(),
                )
            )

        return result

    def _split_large_table(self, table_text: str) -> list[_ChunkUnit]:
        lines = [line.strip() for line in table_text.splitlines() if line.strip()]

        if not lines:
            return []

        table_title = ""

        if lines and self._is_table_title(lines[0]):
            table_title = lines[0]
            lines = lines[1:]

        if len(lines) <= 2:
            return [_ChunkUnit(_UnitKind.TABLE, table_text)]

        header = lines[0]

        has_separator = len(lines) > 1 and self._is_markdown_separator(lines[1])
        separator = lines[1] if has_separator else ""
        body_rows = lines[2:] if has_separator else lines[1:]

        base_lines = []

        if table_title:
            base_lines.append(table_title)

        base_lines.append(header)

        if separator:
            base_lines.append(separator)

        result: list[_ChunkUnit] = []
        current_rows: list[str] = []

        for row in body_rows:
            row_with_header = "\n".join(base_lines + [row])

            if self._token_len(row_with_header) > self._chunk_size:
                if current_rows:
                    result.append(
                        _ChunkUnit(
                            _UnitKind.TABLE,
                            "\n".join(base_lines + current_rows).strip(),
                        )
                    )
                    current_rows = []

                row_as_text = self._markdown_row_to_plain_text(header, row)

                if table_title:
                    row_as_text = f"{table_title}\n\n{row_as_text}"

                result.extend(
                    self._split_large_text_unit(_ChunkUnit(_UnitKind.TEXT, row_as_text))
                )
                continue

            candidate = "\n".join(base_lines + current_rows + [row])

            if current_rows and self._token_len(candidate) > self._chunk_size:
                result.append(
                    _ChunkUnit(
                        _UnitKind.TABLE,
                        "\n".join(base_lines + current_rows).strip(),
                    )
                )
                current_rows = [row]
            else:
                current_rows.append(row)

        if current_rows:
            result.append(
                _ChunkUnit(
                    _UnitKind.TABLE,
                    "\n".join(base_lines + current_rows).strip(),
                )
            )

        if not result:
            result.append(
                _ChunkUnit(
                    _UnitKind.TABLE,
                    "\n".join(base_lines).strip(),
                )
            )

        return result

    def _merge_units(self, units: list[_ChunkUnit]) -> list[str]:
        if not units:
            return []

        chunks: list[str] = []
        current_units: list[_ChunkUnit] = []

        for unit in units:
            if not current_units:
                current_units = [unit]

                if self._units_token_len(current_units) > self._chunk_size:
                    self._flush_units(chunks, current_units)
                    current_units = []

                continue

            candidate_units = current_units + [unit]

            if self._units_token_len(candidate_units) <= self._chunk_size:
                current_units = candidate_units
                continue

            self._flush_units(chunks, current_units)

            overlap_units = self._extract_overlap_units(current_units)
            current_units = overlap_units + [unit]

            if self._units_token_len(current_units) > self._chunk_size:
                current_units = [unit]

            if self._units_token_len(current_units) > self._chunk_size:
                self._flush_units(chunks, current_units)
                current_units = []

        if current_units:
            self._flush_units(chunks, current_units)

        return chunks

    def _flush_units(
        self,
        chunks: list[str],
        units: list[_ChunkUnit],
    ) -> None:
        text = "\n\n".join(unit.text.strip() for unit in units if unit.text.strip())
        text = self._cleanup_chunk_text(text)

        if not self._is_useful_chunk(text):
            return

        chunks.append(text)

    def _extract_overlap_units(self, units: list[_ChunkUnit]) -> list[_ChunkUnit]:
        if self._overlap <= 0:
            return []

        result: list[_ChunkUnit] = []
        total_tokens = 0

        for unit in reversed(units):
            if unit.kind in {
                _UnitKind.TABLE,
                _UnitKind.PAGE,
                _UnitKind.NOTES,
            }:
                continue

            unit_tokens = self._token_len(unit.text)

            if total_tokens + unit_tokens > self._overlap:
                break

            result.insert(0, unit)
            total_tokens += unit_tokens

        return result

    def _units_token_len(self, units: list[_ChunkUnit]) -> int:
        text = "\n\n".join(unit.text for unit in units if unit.text.strip())
        return self._token_len(text)

    def _token_len(self, text: str) -> int:
        return len(self._encoding.encode(text))

    @staticmethod
    def _cleanup_chunk_text(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(r"^\|\s*---.*\n", "", text)

        return text.strip()

    @staticmethod
    def _is_useful_chunk(text: str) -> bool:
        stripped = text.strip()

        if not stripped:
            return False

        if stripped == "Примечания:":
            return False

        if re.fullmatch(r"##\s+Страница\s+\d+", stripped):
            return False

        if re.fullmatch(r"#{1,6}\s+Таблица\s+\d+", stripped):
            return False

        if len(stripped) < 40 and not stripped.startswith("|"):
            return False

        return True

    @staticmethod
    def _restore_newlines_inside_block(text: str) -> str:
        text = re.sub(
            r"\s+([1-9](?:\.\d+){1,6}\.?\s+(?=[А-ЯЁA-Z]))",
            r"\n\1",
            text,
        )

        text = re.sub(
            r"\s+([IVXLCDM]{1,8}\.\s+[А-ЯЁA-Z])",
            r"\n\n\1",
            text,
        )

        text = re.sub(
            r"\s+(ПРИЛОЖЕНИЕ\s+\d+)",
            r"\n\n\1",
            text,
            flags=re.IGNORECASE,
        )

        return text.strip()

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        raw_parts = SENTENCE_SPLIT_RE.split(text)

        sentences: list[str] = []
        buffer = ""

        for part in raw_parts:
            part = part.strip()

            if not part:
                continue

            buffer = f"{buffer} {part}" if buffer else part

            match = re.search(r"(\w+)\.\s*$", buffer)

            if match and match.group(1).lower() in ABBR_SET:
                continue

            if re.search(r"\d\.\s*$", buffer):
                continue

            sentences.append(buffer)
            buffer = ""

        if buffer:
            sentences.append(buffer)

        return sentences

    @staticmethod
    def _is_page_marker(line: str) -> bool:
        return bool(re.match(r"^##\s+Страница\s+\d+$", line.strip()))

    @staticmethod
    def _is_notes_header(line: str) -> bool:
        return line.strip() == "Примечания:"

    @staticmethod
    def _is_table_title(line: str) -> bool:
        return bool(re.fullmatch(r"#{1,6}\s+Таблица\s+\d+", line.strip()))

    @staticmethod
    def _is_table_line(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("|") and stripped.endswith("|")

    @staticmethod
    def _is_markdown_separator(line: str) -> bool:
        stripped = line.strip()

        return bool(
            re.match(
                r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$",
                stripped,
            )
        )

    @staticmethod
    def _is_heading(line: str) -> bool:
        line = line.strip()

        if re.match(r"^#{1,6}\s+\S+", line):
            return True

        if re.match(r"^[IVXLCDM]{1,8}\.\s+[А-ЯЁA-Z]", line):
            return True

        if re.match(r"^ПРИЛОЖЕНИЕ\s+\d+", line, flags=re.IGNORECASE):
            return True

        letters = re.sub(r"[^А-ЯЁA-Z]", "", line)

        if len(letters) >= 12 and line.upper() == line:
            return True

        return False

    @staticmethod
    def _split_markdown_row(row: str) -> list[str]:
        row = row.strip().strip("|")

        cells: list[str] = []

        for cell in row.split("|"):
            cell = cell.strip()
            cell = re.sub(r"<br\s*/?>", " ", cell, flags=re.IGNORECASE)
            cell = re.sub(r"\s+", " ", cell)
            cells.append(cell.strip())

        return cells

    def _markdown_row_to_plain_text(self, header_row: str, row: str) -> str:
        headers = self._split_markdown_row(header_row)
        cells = self._split_markdown_row(row)

        parts: list[str] = []

        for index, cell in enumerate(cells):
            if not cell:
                continue

            header = (
                headers[index]
                if index < len(headers) and headers[index]
                else f"Колонка {index + 1}"
            )

            parts.append(f"- {header}: {cell}")

        if not parts:
            return row

        return "Строка таблицы:\n" + "\n".join(parts)
