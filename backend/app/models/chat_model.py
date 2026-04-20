from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base
from shared.models import chats_chunks


if TYPE_CHECKING:
    from app.models import MessageModel, UserModel
    from shared.models import DocumentChunk


class ChatModel(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="chats", lazy="joined"
    )
    messages: Mapped[list["MessageModel"]] = relationship(
        "MessageModel",
        back_populates="chat",
        cascade="all, delete-orphan",
    )

    compressed_context: Mapped[str | None] = mapped_column(nullable=True)
    compressed_up_to_message_id: Mapped[int | None] = mapped_column(nullable=True)

    last_total_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    reserve_input_tokens: Mapped[int] = mapped_column(nullable=False, default=0)

    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", secondary=chats_chunks
    )
