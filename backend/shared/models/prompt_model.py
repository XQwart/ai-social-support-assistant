from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base

if TYPE_CHECKING:
    pass


class Prompt(Base):
    """Editable LLM prompt section.

    The primary key is ``key``, matching the Python constant name used
    in ``app.agent.prompts`` (e.g. ``SYSTEM_PROMPT_ROLE``). ``version``
    is monotonically incremented on every update; the full history is
    preserved in :class:`PromptHistory` for diff/rollback.
    """

    __tablename__ = "prompts"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    updated_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PromptHistory(Base):
    """Snapshot of a :class:`Prompt` row before each update.

    Stored for diff rendering in the admin UI. ``version`` is the
    version of the body captured (i.e. the value that was overwritten).
    """

    __tablename__ = "prompt_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    prompt_key: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("prompts.key", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    changed_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
