from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models import ChatModel


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(200))
    second_name: Mapped[str] = mapped_column(String(200))
    place_of_work: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bank_id: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    chats: Mapped[list["ChatModel"]] = relationship(
        "ChatModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
