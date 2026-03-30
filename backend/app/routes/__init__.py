from fastapi import APIRouter

from . import auth_routes, chat_routes, message_routes


router = APIRouter()
router.include_router(auth_routes.router)
router.include_router(chat_routes.router)
router.include_router(message_routes.router)
