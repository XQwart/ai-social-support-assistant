from fastapi import APIRouter

router = APIRouter("/auth")


@router.get("/sber/params")
async def get_params():
    pass


@router.get("/sber/callback")
async def sber_callback():
    pass
