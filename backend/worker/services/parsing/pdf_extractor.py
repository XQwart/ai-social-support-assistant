from __future__ import annotations

import io
import logging
import re

import pdfplumber

logger = logging.getLogger(__name__)


class PdfTextExtractor:
    def extract_text(self, pdf_bytes: bytes, url: str | None = None) -> str | None:
        if not pdf_bytes:
            logger.warning("PDF bytes пустые%s", f": {url}" if url else "")
            return None

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                parts: list[str] = []

                for page_index, page in enumerate(pdf.pages):
                    page_content = self._extract_page_content(page, page_index, url)
                    if page_content:
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
        return text or None

    def _extract_page_content(
        self,
        page,
        page_index: int,
        url: str | None,
    ) -> str:
        page_parts: list[str] = []

        tables = self._extract_tables(page, page_index, url)
        if tables:
            for table in tables:
                table_text = self._table_to_text(table)
                if table_text:
                    page_parts.append(table_text)

        if not page_parts:
            page_text = self._extract_plain_text(page, page_index, url)
            if page_text:
                page_parts.append(page_text)

        return "\n\n".join(page_parts).strip()

    def _extract_tables(
        self,
        page,
        page_index: int,
        url: str | None,
    ) -> list[list[list[str | None]]]:
        try:
            tables = page.extract_tables()
            return tables or []
        except Exception:
            logger.exception(
                "pdfplumber: ошибка извлечения таблиц со страницы %s%s",
                page_index,
                f" ({url})" if url else "",
            )
            return []

    def _extract_plain_text(
        self,
        page,
        page_index: int,
        url: str | None,
    ) -> str:
        try:
            text = page.extract_text() or ""
        except Exception:
            logger.exception(
                "pdfplumber: ошибка извлечения текста со страницы %s%s",
                page_index,
                f" ({url})" if url else "",
            )
            return ""

        return self._clean_text(text)

    @staticmethod
    def _table_to_text(table: list[list[str | None]]) -> str:
        rows: list[str] = []

        for row in table:
            if not row:
                continue

            cleaned_cells: list[str] = []
            for cell in row:
                cell_text = cell or ""
                cell_text = PdfTextExtractor._clean_text(cell_text)
                cleaned_cells.append(cell_text)

            if not any(cleaned_cells):
                continue

            rows.append(" | ".join(cleaned_cells))

        return "\n".join(rows).strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = text.replace("\r", "\n")

        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        text = text.replace("\uf02d", "-")
        text = text.replace("\uf0b7", "-")

        text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)

        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        text = re.sub(r"\s+([,.;:!?])", r"\1", text)

        return text.strip()
