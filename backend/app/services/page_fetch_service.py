from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
import logging
from urllib.parse import urlparse, unquote

import httpx
import trafilatura

from app.exceptions.fetch_exceptions import (
    FetchAbortedError,
    ContentParsingError,
    UrlSafetyError,
)
from app.schemas.page_fetch_schemas import FetchResult, FetchErrorKind
from app.utils import text_utils

if TYPE_CHECKING:
    from app.core.config import Config
    from shared.utils.pdf_extractor import PdfTextExtractor


logger = logging.getLogger(__name__)


class PageFetchService:
    _client: httpx.AsyncClient
    _pdf_extractor: PdfTextExtractor
    _config: Config

    def __init__(
        self, client: httpx.AsyncClient, pdf_extractor: PdfTextExtractor, config: Config
    ) -> None:
        self._client = client
        self._pdf_extractor = pdf_extractor
        self._config = config

    async def fetch_many(self, urls: list[str]) -> list[FetchResult]:
        return await asyncio.gather(*(self.fetch_one(url) for url in urls))

    async def fetch_one(self, url: str) -> FetchResult:
        try:
            body, content_type, final_url = await self._stream_fetch(unquote(url))

            return await asyncio.to_thread(
                self._parse_body, body, content_type, unquote(final_url)
            )
        except UrlSafetyError as exc:
            logger.info("PageFetch: blocked %s: %s", url, exc)
            return FetchResult(url=url, error_kind=FetchErrorKind.BLOCKED)
        except FetchAbortedError as exc:
            logger.info("PageFetch: fetch failed for %s: (%s)", url, str(exc))
            return FetchResult(url=url, error_kind=exc.kind, error_detail=str(exc))
        except ContentParsingError as exc:
            logger.info("PageFetch: parse failed for %s: (%s)", url, str(exc))
            return FetchResult(url=url, error_kind=exc.kind)
        except Exception as exc:
            logger.exception("PageFetch: unexpected error for %s", url)
            return FetchResult(url=url, error_kind=FetchErrorKind.UNEXPECTED)

    async def _stream_fetch(self, url: str) -> tuple[bytes, str, str]:
        async with self._client.stream(
            "GET", url=url, follow_redirects=True
        ) as response:
            try:
                if response.status_code >= 400:
                    raise FetchAbortedError(
                        f"Статус код {response.status_code}.",
                        kind=FetchErrorKind.HTTP_STATUS,
                    )

                content_type = (
                    response.headers.get("content-type", "")
                    .split(";")[0]
                    .strip()
                    .lower()
                )

                bytes_limit = self._config.fetch_body_bytes_limit
                declared_lenght: str = response.headers.get("content-lenght", "")
                if declared_lenght and declared_lenght.isdigit():
                    if int(declared_lenght) > bytes_limit:
                        raise FetchAbortedError(
                            "Объем страницы превосходит лимит",
                            kind=FetchErrorKind.TOO_LARGE,
                        )

                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > bytes_limit:
                        raise FetchAbortedError(
                            "Объем страницы превосходит лимит",
                            kind=FetchErrorKind.TOO_LARGE,
                        )

                    chunks.append(chunk)

                return b"".join(chunks), content_type, str(response.url)
            except httpx.HTTPError as exc:
                raise FetchAbortedError(str(exc), kind=FetchErrorKind.NETWORK) from exc

    def _parse_body(self, body: bytes, content_type: str, url: str) -> FetchResult:
        if "html" in content_type or not content_type:
            return self._parse_html(body, url)
        elif "pdf" in content_type:
            return self._parse_pdf(body, url)

        raise ContentParsingError(
            f"Не поддерживаемый тип документа: content-type={content_type}",
            kind=FetchErrorKind.UNSUPPORTED_TYPE,
        )

    def _parse_html(self, body: bytes, url: str) -> FetchResult:
        tree = trafilatura.load_html(body)

        content = trafilatura.extract(
            tree,
            url=url,
            output_format="markdown",
            include_tables=True,
            include_links=True,
            include_comments=False,
            include_images=False,
            favor_precision=True,
            deduplicate=True,
        )
        if content is None or not (content := content.strip()):
            raise ContentParsingError(
                "Вернулась пустая страница", kind=FetchErrorKind.EMPTY_CONTENT
            )

        meta = trafilatura.extract_metadata(tree, default_url=url)

        return FetchResult(
            url=url,
            title=meta.title.strip() if meta.title else "",
            content=content,
        )

    def _parse_pdf(self, body: bytes, url: str) -> FetchResult:
        text = self._pdf_extractor.extract_text(body, url)
        if not text:
            raise ContentParsingError(
                "Вернулась пустая страница", kind=FetchErrorKind.EMPTY_CONTENT
            )

        return FetchResult(
            url=url,
            title=self._get_pdf_name_from_url(url),
            content=text,
        )

    def _get_pdf_name_from_url(self, url: str) -> str:
        path = urlparse(url).path
        name = path.rsplit("/", 1)[-1]

        return name.removesuffix(".pdf") or "PDF документ"
