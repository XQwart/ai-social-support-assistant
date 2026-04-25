from __future__ import annotations

import io
import logging
import re
from typing import Any, Literal

import pdfplumber

logger = logging.getLogger(__name__)


class PdfTextExtractor:
    TABLE_SETTINGS_LINES: dict[str, Any] = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 3,
        "intersection_tolerance": 5,
    }

    def __init__(
        self,
        *,
        add_page_markers: bool = True,
        remove_page_numbers: bool = True,
        footnote_mode: Literal["separate", "remove", "keep"] = "separate",
    ):
        self.add_page_markers = add_page_markers
        self.remove_page_numbers = remove_page_numbers
        self.footnote_mode = footnote_mode

    def extract_text(self, pdf_bytes: bytes, url: str | None = None) -> str | None:
        if not pdf_bytes:
            logger.warning("PDF bytes пустые%s", f": {url}" if url else "")
            return None

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                parts: list[str] = []

                for page_index, page in enumerate(pdf.pages):
                    page_content = self._extract_page_content(
                        page=page,
                        page_index=page_index,
                        url=url,
                    )

                    if not page_content:
                        continue

                    if self.add_page_markers:
                        parts.append(f"## Страница {page_index + 1}\n\n{page_content}")
                    else:
                        parts.append(page_content)

        except Exception:
            logger.exception(
                "pdfplumber: не удалось открыть PDF%s",
                f": {url}" if url else "",
            )
            return None

        if not parts:
            logger.warning(
                "pdfplumber: не удалось извлечь содержимое из PDF%s",
                f": {url}" if url else "",
            )
            return None

        text = "\n\n".join(parts).strip()
        text = self._clean_final_text(text)

        return text or None

    def _extract_page_content(
        self,
        page,
        page_index: int,
        url: str | None,
    ) -> str:
        tables = self._find_tables(page, page_index, url)

        if not tables:
            return self._extract_plain_text(page, page_index, url)

        page_parts: list[str] = []

        page_x0, page_top, page_x1, page_bottom = page.bbox
        current_top = page_top

        for table_number, table in enumerate(tables, start=1):
            _, table_top, _, table_bottom = table.bbox

            if table_top > current_top + 5:
                text_before = self._extract_text_from_bbox(
                    page=page,
                    bbox=(page_x0, current_top, page_x1, table_top),
                    page_index=page_index,
                    url=url,
                )

                if text_before:
                    page_parts.append(text_before)

            table_markdown = self._extract_table_markdown(
                table=table,
                page_index=page_index,
                table_number=table_number,
                url=url,
            )

            if table_markdown:
                page_parts.append(table_markdown)

            current_top = max(current_top, table_bottom)

        if current_top < page_bottom - 5:
            text_after = self._extract_text_from_bbox(
                page=page,
                bbox=(page_x0, current_top, page_x1, page_bottom),
                page_index=page_index,
                url=url,
            )

            if text_after:
                page_parts.append(text_after)

        if not page_parts:
            return self._extract_plain_text(page, page_index, url)

        return "\n\n".join(page_parts).strip()

    def _find_tables(
        self,
        page,
        page_index: int,
        url: str | None,
    ) -> list[Any]:
        try:
            tables = page.find_tables(table_settings=self.TABLE_SETTINGS_LINES) or []
        except Exception:
            logger.exception(
                "pdfplumber: ошибка поиска таблиц на странице %s%s",
                page_index + 1,
                f" ({url})" if url else "",
            )
            return []

        good_tables: list[Any] = []

        for table in tables:
            if not self._has_table_grid(page, table.bbox):
                continue

            try:
                raw_table = table.extract()
            except Exception:
                logger.exception(
                    "pdfplumber: ошибка чтения таблицы на странице %s%s",
                    page_index + 1,
                    f" ({url})" if url else "",
                )
                continue

            normalized = self._normalize_table(raw_table)

            if self._is_probably_table(normalized):
                good_tables.append(table)

        return self._deduplicate_tables(good_tables)

    @staticmethod
    def _has_table_grid(
        page,
        bbox: tuple[float, float, float, float],
    ) -> bool:
        x0, top, x1, bottom = bbox
        padding = 2

        vertical_edges = 0
        horizontal_edges = 0

        for edge in getattr(page, "edges", []):
            ex0 = float(edge.get("x0", 0))
            ex1 = float(edge.get("x1", 0))
            etop = float(edge.get("top", 0))
            ebottom = float(edge.get("bottom", 0))

            inside_bbox = (
                x0 - padding <= ex0 <= x1 + padding
                and x0 - padding <= ex1 <= x1 + padding
                and top - padding <= etop <= bottom + padding
                and top - padding <= ebottom <= bottom + padding
            )

            if not inside_bbox:
                continue

            width = abs(ex1 - ex0)
            height = abs(ebottom - etop)

            if height > 10 and width < 3:
                vertical_edges += 1

            if width > 20 and height < 3:
                horizontal_edges += 1

        return vertical_edges >= 2 and horizontal_edges >= 2

    @staticmethod
    def _deduplicate_tables(tables: list[Any]) -> list[Any]:
        result: list[Any] = []

        for table in sorted(tables, key=lambda t: (t.bbox[1], t.bbox[0])):
            if not result:
                result.append(table)
                continue

            has_duplicate = any(
                PdfTextExtractor._bbox_overlap_ratio(table.bbox, existing.bbox) > 0.8
                for existing in result
            )

            if not has_duplicate:
                result.append(table)

        return result

    @staticmethod
    def _bbox_overlap_ratio(
        bbox_a: tuple[float, float, float, float],
        bbox_b: tuple[float, float, float, float],
    ) -> float:
        ax0, ay0, ax1, ay1 = bbox_a
        bx0, by0, bx1, by1 = bbox_b

        x_left = max(ax0, bx0)
        y_top = max(ay0, by0)
        x_right = min(ax1, bx1)
        y_bottom = min(ay1, by1)

        if x_right <= x_left or y_bottom <= y_top:
            return 0.0

        intersection = (x_right - x_left) * (y_bottom - y_top)

        area_a = max((ax1 - ax0) * (ay1 - ay0), 1)
        area_b = max((bx1 - bx0) * (by1 - by0), 1)

        return intersection / min(area_a, area_b)

    def _extract_text_from_bbox(
        self,
        page,
        bbox: tuple[float, float, float, float],
        page_index: int,
        url: str | None,
    ) -> str:
        try:
            page_x0, page_top, page_x1, page_bottom = page.bbox

            x0, top, x1, bottom = bbox

            safe_bbox = (
                max(page_x0, x0),
                max(page_top, top),
                min(page_x1, x1),
                min(page_bottom, bottom),
            )

            if safe_bbox[3] <= safe_bbox[1] + 3:
                return ""

            cropped = page.crop(safe_bbox)

            text = (
                cropped.extract_text(
                    x_tolerance=1,
                    y_tolerance=3,
                    layout=False,
                )
                or ""
            )

        except Exception:
            logger.exception(
                "pdfplumber: ошибка извлечения текста из bbox на странице %s%s",
                page_index + 1,
                f" ({url})" if url else "",
            )
            return ""

        return self._clean_text(text)

    def _extract_plain_text(
        self,
        page,
        page_index: int,
        url: str | None,
    ) -> str:
        try:
            text = (
                page.extract_text(
                    x_tolerance=1,
                    y_tolerance=3,
                    layout=False,
                )
                or ""
            )
        except Exception:
            logger.exception(
                "pdfplumber: ошибка извлечения текста со страницы %s%s",
                page_index + 1,
                f" ({url})" if url else "",
            )
            return ""

        return self._clean_text(text)

    def _extract_table_markdown(
        self,
        table,
        page_index: int,
        table_number: int,
        url: str | None,
    ) -> str:
        try:
            raw_table = table.extract()
        except Exception:
            logger.exception(
                "pdfplumber: ошибка извлечения таблицы %s на странице %s%s",
                table_number,
                page_index + 1,
                f" ({url})" if url else "",
            )
            return ""

        rows = self._normalize_table(raw_table)

        if not self._is_probably_table(rows):
            return ""

        markdown = self._table_to_markdown(rows)

        if not markdown:
            return ""

        return f"### Таблица {table_number}\n\n{markdown}"

    @staticmethod
    def _normalize_table(table: list[list[str | None]] | None) -> list[list[str]]:
        if not table:
            return []

        rows: list[list[str]] = []

        max_cols = max((len(row) for row in table if row), default=0)

        if max_cols == 0:
            return []

        for row in table:
            if not row:
                continue

            cleaned_row: list[str] = []

            for cell in row:
                cell_text = cell or ""
                cell_text = PdfTextExtractor._clean_table_cell(cell_text)
                cleaned_row.append(cell_text)

            while len(cleaned_row) < max_cols:
                cleaned_row.append("")

            if any(cell.strip() for cell in cleaned_row):
                rows.append(cleaned_row)

        if not rows:
            return []

        rows = PdfTextExtractor._drop_empty_columns(rows)
        rows = PdfTextExtractor._collapse_sparse_grid_columns(rows)
        rows = PdfTextExtractor._merge_header_continuation_rows(rows)

        rows = [row for row in rows if any(cell.strip() for cell in row)]

        return rows

    @staticmethod
    def _drop_empty_columns(rows: list[list[str]]) -> list[list[str]]:
        if not rows:
            return rows

        max_cols = max(len(row) for row in rows)

        keep_indexes: list[int] = []

        for col_index in range(max_cols):
            has_value = any(
                col_index < len(row) and row[col_index].strip() for row in rows
            )

            if has_value:
                keep_indexes.append(col_index)

        return [
            [
                row[col_index] if col_index < len(row) else ""
                for col_index in keep_indexes
            ]
            for row in rows
        ]

    @staticmethod
    def _collapse_sparse_grid_columns(rows: list[list[str]]) -> list[list[str]]:
        if not rows:
            return rows

        max_cols = max(len(row) for row in rows)

        if max_cols < 4:
            return rows

        normalized: list[list[str]] = []

        for row in rows:
            new_row = row[:]

            while len(new_row) < max_cols:
                new_row.append("")

            normalized.append(new_row)

        result_rows: list[list[str]] = [[] for _ in normalized]

        col_index = 0

        while col_index < max_cols:
            if (
                col_index + 1 < max_cols
                and PdfTextExtractor._should_merge_sparse_columns(
                    normalized,
                    col_index,
                    col_index + 1,
                )
            ):
                for row_index, row in enumerate(normalized):
                    merged = PdfTextExtractor._merge_table_cells(
                        row[col_index],
                        row[col_index + 1],
                    )
                    result_rows[row_index].append(merged)

                col_index += 2
            else:
                for row_index, row in enumerate(normalized):
                    result_rows[row_index].append(row[col_index])

                col_index += 1

        return PdfTextExtractor._drop_empty_columns(result_rows)

    @staticmethod
    def _should_merge_sparse_columns(
        rows: list[list[str]],
        left_index: int,
        right_index: int,
    ) -> bool:
        both_non_empty = 0
        left_non_empty = 0
        right_non_empty = 0

        for row in rows:
            left = row[left_index].strip() if left_index < len(row) else ""
            right = row[right_index].strip() if right_index < len(row) else ""

            if left:
                left_non_empty += 1

            if right:
                right_non_empty += 1

            if left and right:
                both_non_empty += 1

        if left_non_empty == 0 or right_non_empty == 0:
            return False

        if both_non_empty > 0:
            return False

        total_rows = max(len(rows), 1)

        left_ratio = left_non_empty / total_rows
        right_ratio = right_non_empty / total_rows

        return left_ratio < 0.8 and right_ratio < 0.8

    @staticmethod
    def _merge_table_cells(left: str, right: str) -> str:
        left = left.strip()
        right = right.strip()

        if left and right:
            return f"{left}<br>{right}"

        return left or right

    @staticmethod
    def _merge_header_continuation_rows(rows: list[list[str]]) -> list[list[str]]:
        if len(rows) < 2:
            return rows

        first_row = rows[0]
        second_row = rows[1]

        if not PdfTextExtractor._looks_like_header_continuation_row(second_row):
            return rows

        max_cols = max(len(first_row), len(second_row))

        merged_header: list[str] = []

        for index in range(max_cols):
            first = first_row[index] if index < len(first_row) else ""
            second = second_row[index] if index < len(second_row) else ""

            merged_header.append(PdfTextExtractor._merge_table_cells(first, second))

        return [merged_header] + rows[2:]

    @staticmethod
    def _looks_like_header_continuation_row(row: list[str]) -> bool:
        non_empty = [cell.strip() for cell in row if cell.strip()]

        if not non_empty:
            return False

        if any(len(cell) > 35 for cell in non_empty):
            return False

        text = " ".join(non_empty).lower()

        if "выплаты" in text or "работникам" in text or "пенсионерам" in text:
            return False

        header_words = {
            "п/п",
            "подразделение",
            "документы",
            "документов",
            "ответственное",
            "оформление",
        }

        return any(word in text for word in header_words)

    @staticmethod
    def _is_probably_table(rows: list[list[str]]) -> bool:
        if len(rows) < 2:
            return False

        max_cols = max(len(row) for row in rows)

        if max_cols < 2:
            return False

        non_empty_cells = sum(1 for row in rows for cell in row if cell.strip())

        if non_empty_cells < 4:
            return False

        if PdfTextExtractor._looks_like_broken_text_table(rows):
            return False

        return True

    @staticmethod
    def _looks_like_broken_text_table(rows: list[list[str]]) -> bool:
        if len(rows) < 5:
            return False

        suspicious_cells = 0
        total_cells = 0

        for row in rows:
            non_empty = [cell.strip() for cell in row if cell.strip()]

            if len(non_empty) < 3:
                continue

            for cell in non_empty:
                total_cells += 1

                if len(cell) <= 2:
                    suspicious_cells += 1
                    continue

                if re.match(r"^[а-яa-z]{2,}", cell):
                    suspicious_cells += 1

                if re.search(r"[а-яa-z]$", cell) and len(cell) <= 20:
                    suspicious_cells += 1

        if total_cells == 0:
            return False

        return suspicious_cells / total_cells > 0.65

    @staticmethod
    def _table_to_markdown(rows: list[list[str]]) -> str:
        if not rows:
            return ""

        max_cols = max(len(row) for row in rows)

        normalized_rows: list[list[str]] = []

        for row in rows:
            normalized_row = row[:]

            while len(normalized_row) < max_cols:
                normalized_row.append("")

            normalized_rows.append(normalized_row)

        header = normalized_rows[0]

        header = [
            cell.strip() if cell.strip() else f"column_{index + 1}"
            for index, cell in enumerate(header)
        ]

        body = normalized_rows[1:]

        lines = [
            "| "
            + " | ".join(
                PdfTextExtractor._escape_markdown_cell(cell) for cell in header
            )
            + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]

        for row in body:
            lines.append(
                "| "
                + " | ".join(
                    PdfTextExtractor._escape_markdown_cell(cell) for cell in row
                )
                + " |"
            )

        return "\n".join(lines).strip()

    @staticmethod
    def _escape_markdown_cell(text: str) -> str:
        text = text.replace("|", "\\|")
        text = text.replace("\n", "<br>")
        return text.strip()

    @staticmethod
    def _clean_table_cell(text: str) -> str:
        text = PdfTextExtractor._clean_text(text)
        text = re.sub(r"\n+", "<br>", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = text.replace("\r", "\n")

        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)

        text = text.replace("\uf02d", "-")
        text = text.replace("\uf0b7", "-")

        text = re.sub(r"(?<=\w)-\n(?=\w)", "-", text)

        lines: list[str] = []

        for raw_line in text.splitlines():
            line = re.sub(r"[ \t]+", " ", raw_line).strip()

            if line:
                lines.append(line)

        if not lines:
            return ""

        blocks: list[str] = []

        for line in lines:
            if not blocks:
                blocks.append(line)
                continue

            previous = blocks[-1]

            if line.startswith("- "):
                item = line[2:].strip()

                if previous.endswith(":"):
                    blocks.append(line)
                    continue

                if re.match(r"^\d+(?:\.\d+)*\.?\s+", item):
                    blocks.append(line)
                    continue

                if re.match(r"^п\.?\s*\d+", item, flags=re.IGNORECASE):
                    blocks[-1] = f"{previous} - {item}"
                    continue

                if not re.search(r"[.;:!?)]$", previous):
                    blocks[-1] = f"{previous} - {item}"
                    continue

                blocks.append(line)
                continue

            if PdfTextExtractor._starts_new_text_block(line):
                blocks.append(line)
                continue

            if PdfTextExtractor._looks_like_numbered_clause(line):
                blocks.append(line)
                continue

            blocks[-1] = f"{previous} {line}"

        text = "\n".join(blocks)

        text = PdfTextExtractor._restore_structural_newlines(text)

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)

        return text.strip()

    @staticmethod
    def _starts_new_text_block(line: str) -> bool:
        line = line.strip()

        if not line:
            return False

        if re.match(r"^[-•]\s+", line):
            return True

        if PdfTextExtractor._looks_like_numbered_clause(line):
            return True

        if re.match(r"^[IVXLCDM]{1,8}\.\s+[А-ЯЁA-Z]", line):
            return True

        letters = re.sub(r"[^А-ЯЁA-Z]", "", line)

        if len(letters) >= 12 and line.upper() == line:
            return True

        if re.match(r"^ПРИЛОЖЕНИЕ\s+\d+", line, flags=re.IGNORECASE):
            return True

        return False

    @staticmethod
    def _looks_like_numbered_clause(line: str) -> bool:
        return bool(
            re.match(
                r"^[1-9](?:\.\d+){1,5}\.?\s*[А-ЯЁA-Zа-яёa-z«(]",
                line.strip(),
            )
        )

    @staticmethod
    def _restore_structural_newlines(text: str) -> str:
        text = re.sub(
            r"\s+([IVXLCDM]{1,8}\.\s+[А-ЯЁA-Z][А-ЯЁA-Z\s,()/-]{8,})",
            r"\n\n\1",
            text,
        )

        text = re.sub(
            r"\s+(ПРИЛОЖЕНИЕ\s+\d+)",
            r"\n\n\1",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s+([1-9](?:\.\d+){1,5}\.?\s*(?=[А-ЯЁA-Z]))",
            r"\n\1",
            text,
        )

        return text.strip()

    def _clean_final_text(self, text: str) -> str:
        text = self._cleanup_common_pdf_artifacts(text)

        if self.remove_page_numbers:
            text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)

            text = re.sub(
                r"\s+\d{1,4}(?=\n\n## Страница|\Z)",
                "",
                text,
            )

        footnote_mode = self.footnote_mode

        if footnote_mode == "separate" or footnote_mode == "remove":
            text = self._process_page_footnotes(
                text=text,
                mode=footnote_mode,
            )

        text = self._cleanup_common_pdf_artifacts(text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def _cleanup_common_pdf_artifacts(text: str) -> str:
        text = re.sub(
            r"(?<=[А-Яа-яЁё])\d{1,2}(?=\s+[а-яё])",
            "",
            text,
        )

        text = re.sub(
            r"\b(\d{1,3})\s+(\d)\s+(\d{2})(?=\s+(?:рублей|руб\.?|₽))",
            r"\1 \2\3",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\b(не\s+менее)(?=\d)",
            r"\1 ",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"-\s*\n(\d+(?:\.\d+)+\.?\s+настоящего)",
            r"- \1",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"(/\d+/)и\s+(/\d+/)",
            r"\1 и \2",
            text,
        )

        return text

    def _process_page_footnotes(
        self,
        text: str,
        mode: Literal["separate", "remove"],
    ) -> str:
        if "## Страница" not in text:
            return self._process_footnotes_in_single_page(text, mode)

        chunks = re.split(r"(?=## Страница\s+\d+)", text)

        processed_chunks: list[str] = []

        for chunk in chunks:
            chunk = chunk.strip()

            if not chunk:
                continue

            processed_chunks.append(self._process_footnotes_in_single_page(chunk, mode))

        return "\n\n".join(processed_chunks).strip()

    def _process_footnotes_in_single_page(
        self,
        page_text: str,
        mode: Literal["separate", "remove"],
    ) -> str:
        page_text = page_text.strip()

        if not page_text:
            return ""

        match = self._find_trailing_footnote_start(page_text)

        if not match:
            return page_text

        main_text = page_text[: match.start()].strip()
        footnotes = page_text[match.start() :].strip()

        footnotes = self._format_footnotes(footnotes)

        if mode == "remove":
            return main_text

        if not footnotes:
            return main_text

        return f"{main_text}\n\nПримечания:\n{footnotes}".strip()

    @staticmethod
    def _find_trailing_footnote_start(text: str) -> re.Match[str] | None:
        pattern = re.compile(r"(?<=[.!?;])\s+(\d{1,2}\s+[А-ЯЁ][^#\n]{30,})")

        matches = list(pattern.finditer(text))

        if not matches:
            return None

        min_start = int(len(text) * 0.55)

        for match in matches:
            if match.start() >= min_start:
                return match

        return None

    @staticmethod
    def _format_footnotes(footnotes: str) -> str:
        footnotes = footnotes.strip()

        footnotes = re.sub(
            r"\s+(?=\d{1,2}\s+[А-ЯЁ])",
            "\n",
            footnotes,
        )

        lines: list[str] = []

        for line in footnotes.splitlines():
            line = line.strip()

            if line:
                lines.append(line)

        return "\n".join(lines)
