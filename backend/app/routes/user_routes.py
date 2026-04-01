from fastapi import APIRouter

from app.dependencies.auth import AuthDep
from app.dependencies.services import UserServiceDep
from app.schemas.user_schemas import UserOut


router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me")
async def me(token_data: AuthDep, user_service: UserServiceDep) -> UserOut:
    user = await user_service.get_by_id(user_id=token_data.user_id)

    return UserOut.model_validate(user)
