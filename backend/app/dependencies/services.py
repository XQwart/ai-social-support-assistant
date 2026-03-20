from typing import Annotated

from fastapi import Depends

from app.services.auth import AuthService


def get_auth_service() -> AuthService:
    return AuthService()


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
