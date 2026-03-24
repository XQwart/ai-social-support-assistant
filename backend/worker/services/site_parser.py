import logging
import re
from typing import Optional
from playwright.sync_api import sync_playwright
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def parse_site(url: str, timeout: float = DEFAULT_TIMEOUT) -> Optional[str]:

    html = None

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            verify=False,
        ) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            html = response.text
    except httpx.TimeoutException:
        logger.warning("Таймаут при загрузке %s", url)
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP ошибка %s при загрузке %s", e.response.status_code, url)
    except Exception:
        logger.exception("Ошибка при загрузке %s", url)

    if html:
        text = _extract_text(html, url)
        if text:
            return text

    html = _fetch_with_playwright(url, timeout)
    if html:
        text = _extract_text(html, url)
        if text:
            return text

    logger.warning("Не удалось извлечь текст с %s", url)
    return None


def _extract_text(html: str, url: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html, "lxml")
        body = soup.find("body")

        if not body:
            logger.warning("Не найден <body> на %s", url)
            return None

        for tag in body.find_all(
            ["script", "style", "nav", "footer", "header", "noscript"]
        ):
            tag.decompose()

        text = body.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 50:
            logger.warning("Мало текста на %s (длина %d)", url, len(text))
            return None

        return text

    except Exception:
        logger.exception("Ошибка парсинга HTML с %s", url)
        return None


def _fetch_with_playwright(url: str, timeout: float) -> Optional[str]:

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = browser.new_page(
                user_agent=USER_AGENT,
                ignore_https_errors=True,
            )
            page.route(
                re.compile(r"\.(png|jpg|jpeg|gif|webp|svg|woff2?|ttf|mp4)$", re.I),
                lambda route: route.abort(),
            )
            page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            return html
    except Exception:
        logger.exception("Playwright: ошибка %s", url)
    return None


def parse_site_with_metadata(source: dict) -> list[dict]:
    urls = source.get("urls", [])
    if not urls:
        return []

    results = []
    for entry in urls:
        url = entry.get("url", "")
        if not url:
            continue

        text = parse_site(url)
        if not text:
            continue

        results.append(
            {
                "source_id": source.get("id", ""),
                "source_url": url,
                "source_name": source.get("name", ""),
                "page_label": entry.get("label", ""),
                "region": source.get("region", ""),
                "region_code": source.get("region_code", ""),
                "category": source.get("category", "общие"),
                "text": text,
            }
        )

    return results
