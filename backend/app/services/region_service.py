from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.repositories import RegionRepository


class RegionService:
    _region_rep: RegionRepository

    def __init__(self, region_rep: RegionRepository) -> None:
        self._region_rep = region_rep

    async def get_code_by_name(self, region_name: str | None) -> str | None:
        if not region_name:
            return

        return await self._region_rep.get_code_by_name(region_name)
