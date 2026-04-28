from __future__ import annotations

from shared.models.regions import Region
from worker.repositories.region_repository import RegionRepository


class RegionService:
    def __init__(self, region_repository: RegionRepository) -> None:
        self._region_repository = region_repository

    async def get_or_create(self, code: str, name: str) -> Region:
        return await self._region_repository.get_or_create(code=code, name=name)
