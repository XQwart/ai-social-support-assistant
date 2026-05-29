from fastapi import APIRouter, status

from app.dependencies.auth import AuthDep
from app.dependencies.services import UserServiceDep
from app.schemas.user_schemas import UserMemoryOut, UserOut


router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(token_data: AuthDep, user_service: UserServiceDep) -> UserOut:
    user = await user_service.get_by_id(user_id=token_data.user_id)

    return UserOut.model_validate(user)


@router.get("/memory", status_code=status.HTTP_200_OK)
async def get_memory(token_data: AuthDep, user_service: UserServiceDep) -> UserMemoryOut:
    user = await user_service.get_by_id(user_id=token_data.user_id)

    return UserMemoryOut.model_validate(user)


@router.delete("/memory", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(token_data: AuthDep, user_service: UserServiceDep) -> None:
    await user_service.reset_user_memory(user_id=token_data.user_id)
