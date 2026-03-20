from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.routes import auth
from app.core.config import get_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()

    engine = create_async_engine(config.database_url)
    session_maker = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    app.state.db_engine = engine
    app.state.session_maker = session_maker

    yield

    engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
