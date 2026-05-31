from __future__ import annotations
from typing import TYPE_CHECKING
import logging

import httpx
from app.schemas.web_search_schemas import WebSearchResult
from app.exceptions.base_exceptions import ExternalServiceError

if TYPE_CHECKING:
    from app.core.config import Config


logger = logging.getLogger(__name__)


class WebSearchService:
    _client: httpx.AsyncClient
    _config: Config

    def __init__(self, client: httpx.AsyncClient, config: Config) -> None:
        self._client = client
        self._config = config

    async def search(self, query: str) -> WebSearchResult:
        try:
            res = await self._client.get(
                url=f"{self._config.searxng_url}/search",
                params={"q": query, "format": "json", "language": "ru"},
                headers={"Accept": "application/json"},
            )

            res.raise_for_status()
        except httpx.ReadTimeout as exc:
            raise ExternalServiceError("Поисковый сервис не ответил вовремя") from exc
        except httpx.ConnectError as exc:
            raise ExternalServiceError("Поисковый сервис недоступен") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ExternalServiceError(
                    "Превышен лимит запросов"
                ) from exc
            raise ExternalServiceError(
                f"Поисковый сервис вернул ошибку. "
                f"status={exc.response.status_code} body={exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Ошибка поиска: {exc!r}") from exc

        return WebSearchResult(**res.json())
