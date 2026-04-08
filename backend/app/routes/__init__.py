from fastapi import APIRouter

from . import auth_routes, chat_routes, message_routes, user_routes


router = APIRouter(prefix="/api")
router.include_router(auth_routes.router)
router.include_router(chat_routes.router)
router.include_router(message_routes.router)
router.include_router(user_routes.router)
