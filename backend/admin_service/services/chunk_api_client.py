from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


class ChunkApiError(Exception):
    pass


class ChunkApiClient:
    _client: httpx.AsyncClient
    _base_url: str

    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def add_text(
        self,
        *,
        source_url: str,
        text: str,
        source_name: str | None = None,
        region_code: str | None = None,
        region_name: str | None = None,
        place_of_work: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/text",
            json={
                "source_url": source_url,
                "source_name": source_name,
                "region_code": region_code,
                "region_name": region_name,
                "place_of_work": place_of_work,
                "text": text,
            },
        )

    async def update_chunk(
        self,
        *,
        chunk_id: int,
        text: str,
        place_of_work: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "PATCH",
            f"/api/v1/chunks/{chunk_id}",
            json={
                "text": text,
                "place_of_work": place_of_work,
            },
        )

    async def delete_chunk(self, chunk_id: int) -> dict[str, Any]:
        return await self._request(
            "DELETE",
            f"/api/v1/chunks/{chunk_id}",
        )

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = await self._client.request(method, url, json=json)
        except httpx.HTTPError as exc:
            logger.exception("ChunkApiClient: request failed %s %s", method, url)
            raise ChunkApiError(f"Не удалось обратиться к chunk-api: {exc}") from exc

        if response.is_error:
            raise ChunkApiError(self._format_error(response))

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise ChunkApiError(
                f"chunk-api вернул не-JSON ответ ({response.status_code})."
            ) from exc

    @staticmethod
    def _format_error(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text or ""

        if isinstance(payload, dict):
            detail = payload.get("detail")
            if detail:
                return f"chunk-api {response.status_code}: {detail}"
        return f"chunk-api {response.status_code}: {payload}"
