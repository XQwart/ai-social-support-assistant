from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup, Tag
from worker.schemas.document import DiscoveredLink
from worker.utils.document_type import detect_document_type
from worker.core.constants import (
    SKIP_EXTENSIONS,
    SKIP_PATH_PATTERNS,
    SKIP_QUERY_KEYS,
    SKIP_SCHEMES,
)


class HtmlLinkExtractor:
    def extract_links(
        self,
        source_id: int,
        html: str,
        base_url: str,
        depth: int,
    ) -> list[DiscoveredLink]:
        soup = BeautifulSoup(html, "lxml")
        found: dict[str, DiscoveredLink] = {}

        for tag in soup.find_all("a", href=True):
            href = self._get_href(tag)
            if not href:
                continue

            normalized = self._normalize_href(href, base_url)
            if not normalized:
                continue

            if not self._is_allowed_url(normalized, base_url):
                continue

            found[normalized] = DiscoveredLink(
                source_id=source_id,
                url=normalized,
                depth=depth,
                document_type=detect_document_type(normalized),
            )

        return sorted(found.values(), key=lambda item: item.url)

    @staticmethod
    def _get_href(tag: Tag) -> str:
        href_value = tag.get("href")

        if isinstance(href_value, list):
            return " ".join(str(item) for item in href_value).strip()

        if isinstance(href_value, str):
            return href_value.strip()

        return ""

    def _normalize_href(self, href: str, base_url: str) -> str | None:
        href = href.strip()
        if not href:
            return None

        parsed = urlparse(href)
        if parsed.scheme and parsed.scheme.lower() in SKIP_SCHEMES:
            return None

        absolute = urljoin(base_url, href)
        return self._normalize_url(absolute)

    def _normalize_url(self, url: str) -> str:
        url = url.strip()

        url = re.sub(r"#:\~:text=.*$", "", url)

        parsed = urlparse(url)

        query_parts: list[str] = []
        if parsed.query:
            for part in parsed.query.split("&"):
                if not part:
                    continue

                key = part.split("=", 1)[0].lower()
                if key in SKIP_QUERY_KEYS:
                    continue

                query_parts.append(part)

        clean_query = "&".join(query_parts)

        normalized = parsed._replace(
            fragment="",
            query=clean_query,
        )
        cleaned = urlunparse(normalized)

        if cleaned.endswith("/") and normalized.path not in ("", "/"):
            cleaned = cleaned.rstrip("/")

        return cleaned

    def _is_allowed_url(self, url: str, base_url: str) -> bool:
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)

        if parsed_url.scheme not in {"http", "https"}:
            return False

        if parsed_url.netloc.lower() != parsed_base.netloc.lower():
            return False

        path = (parsed_url.path or "").lower()

        if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
            return False

        if any(pattern.search(path) for pattern in SKIP_PATH_PATTERNS):
            return False

        return True
