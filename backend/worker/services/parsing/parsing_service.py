from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from worker.schemas.document import ParsedDocument
from worker.services.parsing.pdf_extractor import PdfTextExtractor
from worker.services.parsing.text_extractor import HtmlTextExtractor
from worker.services.parsing.web_fetcher import WebPageFetcher

logger = logging.getLogger(__name__)


class DocumentParsingService:
    def __init__(
        self,
        fetcher: WebPageFetcher,
        text_extractor: HtmlTextExtractor,
        pdf_extractor: PdfTextExtractor,
    ) -> None:
        self._fetcher = fetcher
        self._text_extractor = text_extractor
        self._pdf_extractor = pdf_extractor

    def parse_source(
        self,
        source_id: int,
        url: str,
        name: str | None,
        document_type: str,
    ) -> ParsedDocument | None:
        if not url:
            logger.warning("Source %d: пустой URL", source_id)
            return None

        if document_type == "pdf":
            text = self._parse_pdf(url)
        else:
            text = self._parse_html(url)

        if not text:
            return None

        return ParsedDocument(
            source_id=source_id,
            source_url=url,
            source_name=name,
            text=text,
        )

    def close(self) -> None:
        self._fetcher.close()

    def _parse_pdf(self, url: str) -> str | None:
        if self._is_web_url(url):
            pdf_bytes = self._fetcher.get_bytes(url)
            if not pdf_bytes:
                return None

            return self._pdf_extractor.extract_text(pdf_bytes, url)

        file_path = Path(url)
        if not file_path.exists():
            logger.warning("PDF файл не найден: %s", file_path)
            return None

        try:
            pdf_bytes = file_path.read_bytes()
        except Exception:
            logger.exception("Ошибка чтения PDF файла: %s", file_path)
            return None

        return self._pdf_extractor.extract_text(pdf_bytes, str(file_path))

    def _parse_html(self, url: str) -> str | None:
        html = self._fetcher.get_html(url)
        if not html:
            return None

        return self._text_extractor.extract_text(html, url)

    @staticmethod
    def _is_web_url(url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"}
