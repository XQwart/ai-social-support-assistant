import logging
import re

import httpx
from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Browser, Playwright, sync_playwright

from worker.core.constants import USER_AGENT
from worker.schemas.document import ParsedDocument
from worker.core.constants import (
    _NOISE_CLASS_RE,
    _NOISE_ROLES,
    _NOISE_TAGS,
    _MIN_TEXT_LENGTH,
    _BLOCKED_RESOURCES_RE,
)

logger = logging.getLogger(__name__)


class ParsingService:
    _default_timeout: int
    _pw_: Playwright | None
    _browser_: Browser | None

    def __init__(self, default_timeout: int = 30) -> None:
        self._default_timeout = default_timeout
        self._pw_: Playwright | None = None
        self._browser_: Browser | None = None

    def parse_source(
        self,
        source_id: int,
        url: str,
        name: str,
    ) -> ParsedDocument | None:
        if not url:
            logger.warning("Source %d: пустой URL", source_id)
            return None

        text = self._parse_site(url)
        if not text:
            return None

        return ParsedDocument(
            source_id=source_id,
            source_url=url,
            source_name=name,
            text=text,
        )

    def close(self) -> None:
        self._close_browser()

    def _parse_site(self, url: str) -> str | None:

        html = self._fetch_with_httpx(url)
        if html:
            text = self._extract_text(html, url)
            if text:
                return text

        html = self._fetch_with_playwright(url)
        if html:
            text = self._extract_text(html, url)
            if text:
                return text

        logger.warning("Не удалось извлечь текст с %s", url)
        return None

    def _fetch_with_httpx(self, url: str) -> str | None:
        for verify_ssl in (True, False):
            try:
                with httpx.Client(
                    timeout=self._default_timeout,
                    follow_redirects=True,
                    verify=verify_ssl,
                ) as client:
                    response = client.get(url, headers={"User-Agent": USER_AGENT})
                    response.raise_for_status()

                    if not verify_ssl:
                        logger.warning("SSL отключён для %s", url)

                    return self._decode_response(response)

            except (httpx.ConnectError, httpx.ConnectTimeout):
                if verify_ssl:
                    logger.debug("SSL ошибка для %s, пробуем без верификации", url)
                    continue
                logger.warning("Не удалось подключиться к %s", url)
                return None

            except httpx.TimeoutException:
                logger.warning("Таймаут при загрузке %s", url)
                return None

            except httpx.HTTPStatusError as exc:
                logger.warning("HTTP %d: %s", exc.response.status_code, url)
                return None

            except Exception:
                logger.exception("Ошибка при загрузке %s", url)
                return None

        return None

    @staticmethod
    def _decode_response(response: httpx.Response) -> str:
        if response.charset_encoding:
            return response.text

        raw = response.content
        head = raw[:2000].lower()

        if b"windows-1251" in head:
            return raw.decode("windows-1251", errors="replace")
        if b"koi8-r" in head:
            return raw.decode("koi8-r", errors="replace")
        if b"cp866" in head:
            return raw.decode("cp866", errors="replace")

        return response.text

    def _get_browser(self) -> Browser:
        if self._browser_ is None:
            self._pw_ = sync_playwright().start()
            self._browser_ = self._pw_.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                ],
            )
        return self._browser_

    def _fetch_with_playwright(self, url: str) -> str | None:
        try:
            browser = self._get_browser()
            context = browser.new_context(
                user_agent=USER_AGENT,
                ignore_https_errors=True,
            )
            try:
                page = context.new_page()

                page.route(_BLOCKED_RESOURCES_RE, lambda route: route.abort())

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self._default_timeout * 1000,
                )

                try:
                    page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass

                try:
                    page.wait_for_selector(
                        "body > *:not(script):not(style)",
                        state="attached",
                        timeout=5_000,
                    )
                except Exception:
                    pass

                return page.content()
            finally:
                context.close()

        except Exception:
            logger.exception("Playwright: ошибка при загрузке %s", url)
            self._close_browser()
            return None

    def _close_browser(self) -> None:
        if self._browser_:
            try:
                self._browser_.close()
            except Exception:
                pass
            self._browser_ = None

        if self._pw_:
            try:
                self._pw_.stop()
            except Exception:
                pass
            self._pw_ = None

    def _extract_text(self, html: str, url: str) -> str | None:
        try:
            soup = BeautifulSoup(html, "lxml")
            body = soup.find("body")

            if not body:
                logger.warning("Не найден <body> на %s", url)
                return None

            self._remove_noise(body)

            text = body.get_text(separator="\n", strip=True)
            text = self._clean_text(text)

            if len(text) < _MIN_TEXT_LENGTH:
                logger.warning(
                    "Мало текста на %s (%d символов, порог %d)",
                    url,
                    len(text),
                    _MIN_TEXT_LENGTH,
                )
                return None

            return text

        except Exception:
            logger.exception("Ошибка парсинга HTML с %s", url)
            return None

    @staticmethod
    def _remove_noise(body: Tag) -> None:
        for tag_name in _NOISE_TAGS:
            for tag in body.find_all(tag_name):
                tag.decompose()

        for role in _NOISE_ROLES:
            for tag in body.find_all(attrs={"role": role}):
                tag.decompose()

        for tag in body.find_all(True):
            attrs = getattr(tag, "attrs", None) or {}
            classes = " ".join(attrs.get("class", []))
            tag_id = attrs.get("id", "") or ""

            if _NOISE_CLASS_RE.search(f"{classes} {tag_id}"):
                tag.decompose()

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        text = re.sub(r"[^\S\n]+", " ", text)

        return text.strip()
