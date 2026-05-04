from __future__ import annotations
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from admin_service.core.config import get_admin_config
from admin_service.core.security import AdminSessionToken, CSRFTokenSigner
from admin_service.services.bootstrap_service import BootstrapService
from app.core.config import get_config
from app.core.database import create_engine, create_session_maker
from app.core.logger import setup_logging
from app.core.redis import create_redis


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    backend_config = get_config()
    admin_config = get_admin_config()

    setup_logging(level=backend_config.log_level)

    engine = create_engine(backend_config)
    session_maker = create_session_maker(engine)
    redis = create_redis(backend_config)
    chunk_api_client = httpx.AsyncClient(timeout=admin_config.chunk_api_timeout)

    session_token = AdminSessionToken(
        secret=admin_config.admin_jwt_secret,
        ttl=admin_config.session_ttl,
    )
    csrf_signer = CSRFTokenSigner(secret=admin_config.admin_csrf_secret)

    app.state.db_engine = engine
    app.state.session_maker = session_maker
    app.state.redis = redis
    app.state.chunk_api_client = chunk_api_client
    app.state.session_token = session_token
    app.state.csrf_signer = csrf_signer
    app.state.admin_config = admin_config
    app.state.backend_config = backend_config

    bootstrap = BootstrapService(session_maker=session_maker, config=admin_config)
    await bootstrap.run()

    logger.info("Admin service started successfully")

    try:
        yield
    finally:
        await chunk_api_client.aclose()
        await redis.aclose()
        await engine.dispose()
