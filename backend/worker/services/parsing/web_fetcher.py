from __future__ import annotations

import logging

import httpx
from playwright.sync_api import Browser, Playwright, sync_playwright

from worker.core.constants import USER_AGENT, BLOCKED_RESOURCES_RE

logger = logging.getLogger(__name__)


class WebPageFetcher:
    _default_timeout: int
    _pw: Playwright | None
    _browser: Browser | None
    _client: httpx.Client
    _client_no_ssl: httpx.Client

    def __init__(self, default_timeout: int = 30) -> None:
        self._default_timeout = default_timeout
        self._pw = None
        self._browser = None
        self._client: httpx.Client
        self._client_no_ssl: httpx.Client
        timeout = httpx.Timeout(connect=5, read=default_timeout, write=5, pool=5)
        headers = {"User-Agent": USER_AGENT}

        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            verify=True,
            headers=headers,
        )
        self._client_no_ssl = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            verify=False,
            headers=headers,
        )

    def get_html(self, url: str) -> str | None:
        html = self._fetch_with_httpx(url)
        if html:
            return html

        return self._fetch_with_playwright(url)

    def get_html_fast(self, url: str) -> str | None:
        return self._fetch_with_httpx(url)

    def _fetch_with_httpx(self, url: str) -> str | None:
        response = self._request_with_httpx(url)
        if response is None:
            return None

        content_type = (response.headers.get("content-type") or "").lower()
        if not self._is_html_content_type(content_type):
            logger.debug(
                "URL не похож на HTML по content-type (%s): %s",
                content_type,
                url,
            )
            return None

        return self._decode_response(response)

    def _request_with_httpx(self, url: str) -> httpx.Response | None:
        verify_ssl_variants = [True, False]

        for verify_ssl in verify_ssl_variants:
            try:
                response = self._make_request(
                    url, verify_ssl=verify_ssl, accept_encoding=None
                )
                if not verify_ssl:
                    logger.warning("SSL отключён для %s", url)
                return response

            except httpx.DecodingError:
                logger.warning(
                    "Ошибка декодирования ответа от %s, пробуем без сжатия", url
                )
                try:
                    response = self._make_request(
                        url, verify_ssl=verify_ssl, accept_encoding="identity"
                    )
                    return response
                except Exception:
                    logger.warning(
                        "Повторная попытка без сжатия тоже не удалась: %s", url
                    )
                    return None

            except (httpx.ConnectError, httpx.ConnectTimeout):
                if verify_ssl:
                    logger.debug(
                        "SSL/Connect ошибка для %s, пробуем без верификации", url
                    )
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

    def _make_request(self, url, *, verify_ssl, accept_encoding=None):
        client = self._client if verify_ssl else self._client_no_ssl

        headers = {"Accept-Encoding": accept_encoding} if accept_encoding else {}

        response = client.get(url, headers=headers)
        response.raise_for_status()

        return response

    def get_bytes(self, url: str) -> bytes | None:
        response = self._request_with_httpx(url)
        if response is None:
            return None

        return response.content

    @staticmethod
    def _decode_response(response: httpx.Response) -> str:
        raw = response.content
        head = raw[:4000].lower()

        if b"windows-1251" in head:
            return raw.decode("windows-1251", errors="replace")
        if b"koi8-r" in head:
            return raw.decode("koi8-r", errors="replace")
        if b"cp866" in head:
            return raw.decode("cp866", errors="replace")

        if response.encoding:
            try:
                return raw.decode(response.encoding, errors="replace")
            except Exception:
                logger.debug(
                    "Не удалось декодировать ответ через encoding=%s",
                    response.encoding,
                )

        return response.text

    @staticmethod
    def _is_html_content_type(content_type: str) -> bool:
        return "text/html" in content_type or "application/xhtml+xml" in content_type

    def _get_browser(self) -> Browser:
        if self._browser is None:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                ],
            )
        return self._browser

    def _fetch_with_playwright(self, url: str) -> str | None:
        try:
            browser = self._get_browser()
            context = browser.new_context(
                user_agent=USER_AGENT,
                ignore_https_errors=True,
            )

            try:
                page = context.new_page()
                page.route(BLOCKED_RESOURCES_RE, lambda route: route.abort())

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
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None

    def close(self) -> None:
        self._client.close()
        self._client_no_ssl.close()
        self._close_browser()
