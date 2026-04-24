from fastapi import APIRouter

from . import (
    admins_routes,
    auth_routes,
    chunk_routes,
    dashboard_routes,
    prompt_routes,
)


router = APIRouter()
router.include_router(auth_routes.router)
router.include_router(dashboard_routes.router)
router.include_router(prompt_routes.router)
router.include_router(chunk_routes.router)
router.include_router(admins_routes.router)
