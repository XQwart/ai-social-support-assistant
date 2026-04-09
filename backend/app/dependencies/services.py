from typing import Annotated

from fastapi import Depends

from app.dependencies.ai import (
    ChatAIClientDep,
    CompressAIClientDep,
    EmbeddingAIClientDep,
)
from app.dependencies.config import ConfigDep
from app.dependencies.repositories import (
    UserRepoDep,
    TokenRedisRepoDep,
    OauthRepoDep,
    MessageRepoDep,
    ChatRepoDep,
    DocumentRepoDep,
    ChunkRepoDep,
)
from app.dependencies.http import HTTPSberClientDep
from app.dependencies.jwt import AccessTokenDep, RefreshTokenDep
from app.services import (
    AuthService,
    ChatService,
    ConversationService,
    MessageService,
    SberIdService,
    UserService,
    LLMService,
    RAGService,
)


def get_auth_service(
    config: ConfigDep,
    sberid_service: "SberIdServiceDep",
    oauth_rep: OauthRepoDep,
    token_rep: TokenRedisRepoDep,
    user_service: "UserServiceDep",
    access_token_util: AccessTokenDep,
    refresh_token_util: RefreshTokenDep,
) -> AuthService:
    return AuthService(
        config,
        sberid_service,
        oauth_rep,
        token_rep,
        user_service,
        access_token_util,
        refresh_token_util,
    )


def get_sberid_service(
    config: ConfigDep,
    client: HTTPSberClientDep,
) -> SberIdService:
    return SberIdService(config, client)


def get_message_service(message_repo: MessageRepoDep) -> MessageService:
    return MessageService(message_repo)


def get_chat_service(chat_rep: ChatRepoDep) -> ChatService:
    return ChatService(chat_rep)


def get_conversation_service(
    llm_service: "LLMServiceDep",
    message_service: "MessageServiceDep",
    chat_service: "ChatServiceDep",
    config: ConfigDep,
) -> ConversationService:
    return ConversationService(llm_service, message_service, chat_service, config)


def get_user_service(user_rep: UserRepoDep) -> UserService:
    return UserService(user_rep)


def get_llm_service(
    config: ConfigDep,
    chat_client: ChatAIClientDep,
    compress_client: CompressAIClientDep,
    rag_service: "RAGServiceDep",
) -> LLMService:
    return LLMService(config, chat_client, compress_client, rag_service)


def get_rag_service(
    client: EmbeddingAIClientDep,
    document_repo: DocumentRepoDep,
    chunk_repo: ChunkRepoDep,
) -> RAGService:
    return RAGService(client, document_repo, chunk_repo)


LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
ConversationServiceDep = Annotated[
    ConversationService, Depends(get_conversation_service)
]
SberIdServiceDep = Annotated[SberIdService, Depends(get_sberid_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
RAGServiceDep = Annotated[RAGService, Depends(get_rag_service)]
