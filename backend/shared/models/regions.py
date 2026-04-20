from __future__ import annotations


from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Region(Base):
    __tablename__ = "region"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(4), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class SourceRegion(Base):
    __tablename__ = "source_regions"

    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), primary_key=True)

    region_id: Mapped[int] = mapped_column(ForeignKey("region.id"), primary_key=True)
