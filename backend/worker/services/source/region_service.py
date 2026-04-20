from __future__ import annotations

from shared.models.regions import Region
from worker.repositories.region_repository import RegionRepository


class RegionService:
    def __init__(self, region_repository: RegionRepository) -> None:
        self._region_repository = region_repository

    def get_or_create(self, code: str, name: str) -> Region:
        region = self._region_repository.get_by_code(code)

        if region is not None:
            if region.name != name:
                region.name = name
            return region

        return self._region_repository.create(code=code, name=name)
