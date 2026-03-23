from typing import Annotated

from fastapi import Depends

from app.services.chat import ChatService
from app.services.auth import AuthService
from app.services.message import MessageService
from app.dependencies.config import ConfigDep
from app.dependencies.repositories import (
    UserRepoDep,
    TokenRedisRepoDep,
    OauthRepoDep,
    MessageRepoDep,
    ChatRepoDep,
)
from app.dependencies.jwt import AccessTokenDep, RefreshTokenDep


def get_auth_service(
    config: ConfigDep,
    oauth_rep: OauthRepoDep,
    token_rep: TokenRedisRepoDep,
    user_rep: UserRepoDep,
    access_token_util: AccessTokenDep,
    refresh_token_util: RefreshTokenDep,
) -> AuthService:
    return AuthService(
        config, oauth_rep, token_rep, user_rep, access_token_util, refresh_token_util
    )


def get_message_service(message_repo: MessageRepoDep) -> MessageService:
    return MessageService(message_repo)


def get_chat_service(chat_rep: ChatRepoDep) -> ChatService:
    return ChatService(chat_rep)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
