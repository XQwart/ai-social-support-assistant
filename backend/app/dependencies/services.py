from typing import Annotated

from fastapi import Depends

from app.services.auth import AuthService
from app.dependencies.config import ConfigDep
from app.dependencies.repositories import UserRepoDep, TokenRedisRepoDep, OauthRepoDep


def get_auth_service(
    config: ConfigDep,
    oauth_rep: OauthRepoDep,
    token_rep: TokenRedisRepoDep,
    user_rep: UserRepoDep,
) -> AuthService:
    return AuthService(config, oauth_rep, token_rep, user_rep)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
