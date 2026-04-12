from typing import AsyncGenerator, Annotated

from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)


async def get_db_session(req: Request) -> AsyncGenerator[AsyncSession, None]:
    session_maker: async_sessionmaker[AsyncSession] = req.app.state.session_maker

    async with session_maker() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
