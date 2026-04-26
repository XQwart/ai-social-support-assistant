from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from shared.models.regions import Region


class RegionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_code(self, code: str) -> Region | None:
        stmt = select(Region).where(Region.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, code: str, name: str) -> Region:
        stmt = (
            pg_insert(Region)
            .values(
                code=code,
                name=name,
            )
            .on_conflict_do_nothing(
                index_elements=[Region.code],
            )
            .returning(Region.id)
        )

        result = await self._session.execute(stmt)
        inserted_id = result.scalar_one_or_none()

        if inserted_id is not None:
            region = await self._session.get(Region, inserted_id)

            if region is None:
                raise RuntimeError(f"Region {code} inserted but not found")

            return region

        region = await self.get_by_code(code)

        if region is None:
            raise RuntimeError(f"Region {code} not found after conflict")

        if region.name != name:
            region.name = name

        return region
