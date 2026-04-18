from sqlalchemy import Table, Column, Integer, ForeignKey

from shared.database import Base

chats_chunks = Table(
    "chats_chunks",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id"), primary_key=True),
    Column("chunk_id", Integer, ForeignKey("chunks.id"), primary_key=True),
)
