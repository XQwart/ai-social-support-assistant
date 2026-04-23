from __future__ import annotations

from shared.models.regions import Region
from worker.repositories.region_repository import RegionRepository


class RegionService:
    def __init__(self, region_repository: RegionRepository) -> None:
        self._region_repository = region_repository

    async def get_or_create(self, code: str, name: str) -> Region:
        region = await self._region_repository.get_by_code(code)
        if region is not None:
            return region

        return await self._region_repository.create(code=code, name=name)
