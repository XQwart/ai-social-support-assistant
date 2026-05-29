from typing import Annotated

from fastapi import Depends, Request
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_maker = request.app.state.session_maker
    session = session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        session.expunge_all()
        await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_session)]
