from __future__ import annotations
from typing import TYPE_CHECKING

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

if TYPE_CHECKING:
    from app.core.config import Config


async def create_checkpointer(config: Config) -> AsyncPostgresSaver:
    pool = AsyncConnectionPool(
        conninfo=config.database_url.replace("postgresql+asyncpg://", "postgresql://"),
        max_size=config.checkpointer_pool_max_conn,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await pool.open()

    checkpointer = AsyncPostgresSaver(conn=pool)
    await checkpointer.setup()

    return checkpointer
