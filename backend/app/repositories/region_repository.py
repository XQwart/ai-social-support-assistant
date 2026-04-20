from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select

from shared.models import Region

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class RegionRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_code_by_name(self, region_name: str) -> str | None:
        result = await self._session.execute(
            select(Region).where(Region.name == region_name)
        )
        region = result.scalar_one_or_none()

        return region.code if region else None
