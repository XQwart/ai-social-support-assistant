from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base

if TYPE_CHECKING:
    pass


class DocumentChunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("source.id", ondelete="CASCADE"),
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    region_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    place_of_work: Mapped[str | None] = mapped_column(String(255), nullable=True)

    qdrant_point_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
