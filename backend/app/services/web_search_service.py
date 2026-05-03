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
        res = await self._client.get(
            url=f"{self._config.searxng_url}/search",
            params={"q": query, "format": "json", "language": "ru"},
            headers={"Accept": "application/json"},
        )

        if res.status_code != 200:
            logger.error(
                "Search in web failed | status=%s | body=%s",
                res.status_code,
                res.text,
            )
            raise ExternalServiceError("Web search returned malformed response")

        return WebSearchResult(**res.json())
