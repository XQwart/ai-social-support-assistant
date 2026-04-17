from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from worker.models.regions import Region


class RegionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Region | None:
        stmt = select(Region).where(Region.code == code)
        return self._session.scalar(stmt)

    def create(self, code: str, name: str) -> Region:
        region = Region(code=code, name=name)
        self._session.add(region)
        self._session.flush()
        return region
