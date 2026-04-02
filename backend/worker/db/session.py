from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_session(postgres_url: str):
    engine = create_engine(
        postgres_url,
        pool_pre_ping=True,
    )

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    return session_factory
