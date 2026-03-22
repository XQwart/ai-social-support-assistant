from typing import Annotated
from fastapi import Depends

from app.repositories.user import UserRepository
from app.repositories.oauth import OauthRepository
from app.repositories.token import TokenRedisRepository
from app.repositories.chat import ChatRepository
from app.dependencies.config import ConfigDep
from app.dependencies.redis import RedisDep
from app.dependencies.session import DBSessionDep


def get_user_repo(session: DBSessionDep) -> UserRepository:
    return UserRepository(session)


def get_token_redis_repo(config: ConfigDep, redis: RedisDep) -> TokenRedisRepository:
    return TokenRedisRepository(config, redis)


def get_auth_redis_repo(config: ConfigDep, redis: RedisDep) -> OauthRepository:
    return OauthRepository(config, redis)


def get_chat_repo(session: DBSessionDep) -> ChatRepository:
    return ChatRepository(session=session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
TokenRedisRepoDep = Annotated[TokenRedisRepository, Depends(get_token_redis_repo)]
OauthRepoDep = Annotated[OauthRepository, Depends(get_auth_redis_repo)]
ChatRepoDep = Annotated[ChatRepository, Depends(get_chat_repo)]
