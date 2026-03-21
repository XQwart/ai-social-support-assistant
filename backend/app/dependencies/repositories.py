from typing import Annotated
from fastapi import Depends

from app.repositories.user import UserRepository
from app.repositories.oauth import OauthRepository
from app.repositories.token import TokenRedisRepository
from app.dependencies.config import ConfigDep
from app.dependencies.redis import RedisDep
from app.dependencies.session import DBSessionDep


def get_user_repo(config: ConfigDep, session: DBSessionDep) -> UserRepository:
    return UserRepository(config, session)


def get_token_redis_repo(config: ConfigDep, redis: RedisDep) -> TokenRedisRepository:
    return TokenRedisRepository(config, redis)


def get_auth_redis_repo(config: ConfigDep, redis: RedisDep) -> OauthRepository:
    return OauthRepository(config, redis)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
TokenRedisRepoDep = Annotated[TokenRedisRepository, Depends(get_token_redis_repo)]
OauthRepoDep = Annotated[OauthRepository, Depends(get_auth_redis_repo)]
