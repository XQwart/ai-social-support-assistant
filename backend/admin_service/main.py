from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from admin_service.core.config import STATIC_DIR, get_admin_config
from admin_service.core.security import CSRFTokenSigner
from admin_service.exceptions.handlers import init_exception_handlers
from admin_service.lifespan import lifespan
from admin_service.middlewares import (
    AuditContextMiddleware,
    CSRFMiddleware,
    SecurityHeadersMiddleware,
)
from admin_service.routes import router


def create_admin_app() -> FastAPI:
    config = get_admin_config()
    app = FastAPI(
        title="SOC Admin Panel",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
        # When mounted behind nginx at /admin/, ``root_path`` makes
        # ``request.url_for`` and ``app.url_path_for`` emit absolute
        # paths that include the prefix, so generated links and
        # redirects keep the browser inside the admin namespace.
        root_path=config.normalized_base_path,
    )

    # CSRF middleware needs a signer instance up front (lifespan also stores
    # one for DI, but middleware is constructed before lifespan runs).
    csrf_signer = CSRFTokenSigner(secret=config.admin_csrf_secret)

    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

    app.include_router(router)

    init_exception_handlers(app)

    # Order matters: outermost added last. Effective order at request time:
    #   SecurityHeaders -> CSRF -> AuditContext -> route
    app.add_middleware(AuditContextMiddleware)
    app.add_middleware(
        CSRFMiddleware,
        signer=csrf_signer,
        force_https=config.admin_force_https,
        cookie_path=config.cookie_path,
    )
    app.add_middleware(
        SecurityHeadersMiddleware,
        force_https=config.admin_force_https,
    )

    return app


admin_app = create_admin_app()
