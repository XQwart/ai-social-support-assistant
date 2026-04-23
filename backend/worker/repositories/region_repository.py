from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.regions import Region


class RegionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_code(self, code: str) -> Region | None:
        stmt = select(Region).where(Region.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, code: str, name: str) -> Region:
        region = Region(code=code, name=name)
        self._session.add(region)
        await self._session.flush()
        return region
