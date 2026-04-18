from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base
from .associations import chats_chunks

if TYPE_CHECKING:
    from app.models import ChatModel


class DocumentChunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("source.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    chats: Mapped[list["ChatModel"]] = relationship(
        "ChatModel", secondary=chats_chunks, back_populates="document_chunks"
    )
