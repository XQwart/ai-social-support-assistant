import logging
from typing import Optional

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
    """Скачать HTML-страницу и извлечь чистый текст.

    Args:
        url: URL страницы для парсинга
        timeout: таймаут запроса в секундах

    Returns:
        Очищенный текст страницы или None при ошибке
    """
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            verify=False,  # Некоторые гос. сайты имеют проблемы с сертификатами
        ) as client:
            response = client.get(
                url,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            html = response.text

    except httpx.TimeoutException:
        logger.warning("Таймаут при загрузке %s", url)
        return None
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP ошибка %s при загрузке %s", e.response.status_code, url)
        return None
    except Exception as e:
        logger.error("Ошибка при загрузке %s: %s", url, e)
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body")

        if not body:
            logger.warning("Не найден тег <body> на %s", url)
            return None

        # Удаляем ненужные теги
        for tag in body.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = body.get_text(separator=" ", strip=True)

        # Очищаем от лишних пробелов
        import re
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 50:
            logger.warning("Слишком мало текста на %s (длина %d)", url, len(text))
            return None

        return text

    except Exception as e:
        logger.error("Ошибка парсинга HTML с %s: %s", url, e)
        return None


def parse_site_with_metadata(source: dict) -> Optional[dict]:
    """Спарсить сайт и вернуть структурированный результат.

    Args:
        source: словарь из sources.json с полями id, url, region и т.д.

    Returns:
        Словарь с метаданными и текстом, или None при ошибке
    """
    url = source.get("url", "")
    if not url:
        return None

    text = parse_site(url)
    if not text:
        return None

    return {
        "source_id": source.get("id", ""),
        "source_url": url,
        "source_name": source.get("name", ""),
        "region": source.get("region", ""),
        "region_code": source.get("region_code", ""),
        "category": source.get("category", "общие"),
        "text": text,
    }
