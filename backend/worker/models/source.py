from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Source(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)

    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    crawl_interval_minutes: Mapped[int] = mapped_column(default=60, nullable=False)

    next_crawl_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    is_locked: Mapped[bool] = mapped_column(default=False, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    document_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="html",
    )
    place_of_work: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
