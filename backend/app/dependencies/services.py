from typing import Annotated

from fastapi import Depends

from app.dependencies.ai import (
    ChatLLMClientDep,
    CompressLLMClientDep,
    EmbeddingClientDep,
)
from app.dependencies.agent import CheckpointerDep
from app.dependencies.config import ConfigDep
from app.dependencies.repositories import (
    UserRepoDep,
    TokenRedisRepoDep,
    OauthRepoDep,
    MessageRepoDep,
    ChatRepoDep,
    DocumentRepoDep,
    ChunkRepoDep,
    RegionRepoDep,
)
from app.dependencies.http import HTTPSberClientDep
from app.dependencies.jwt import AccessTokenDep, RefreshTokenDep
from app.services import (
    AgentService,
    AuthService,
    ChatService,
    ConversationService,
    MessageService,
    SberIdService,
    UserService,
    RAGService,
    RegionService,
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


def get_sberid_service(config: ConfigDep, client: HTTPSberClientDep) -> SberIdService:
    return SberIdService(config, client)


def get_message_service(message_repo: MessageRepoDep) -> MessageService:
    return MessageService(message_repo)


def get_chat_service(chat_rep: ChatRepoDep) -> ChatService:
    return ChatService(chat_rep)


def get_user_service(user_rep: UserRepoDep) -> UserService:
    return UserService(user_rep)


def get_region_service(region_rep: RegionRepoDep) -> RegionService:
    return RegionService(region_rep)


def get_conversation_service(
    agent_service: "AgentServiceDep",
    message_service: "MessageServiceDep",
    chat_service: "ChatServiceDep",
    rag_service: "RAGServiceDep",
    user_service: "UserServiceDep",
    region_service: "RegionServiceDep",
    config: ConfigDep,
) -> ConversationService:
    return ConversationService(
        agent_service,
        message_service,
        chat_service,
        rag_service,
        user_service,
        region_service,
        config,
    )


def get_agent_service(
    chat_llm: ChatLLMClientDep,
    compress_llm: CompressLLMClientDep,
    region_service: "RegionServiceDep",
    rag_service: "RAGServiceDep",
    user_service: "UserServiceDep",
    checkpointer: CheckpointerDep,
    config: ConfigDep,
) -> AgentService:
    return AgentService(
        chat_llm,
        compress_llm,
        region_service,
        rag_service,
        user_service,
        checkpointer,
        config,
    )


def get_rag_service(
    client: EmbeddingClientDep,
    document_repo: DocumentRepoDep,
    chunk_repo: ChunkRepoDep,
) -> RAGService:
    return RAGService(client, document_repo, chunk_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
ConversationServiceDep = Annotated[
    ConversationService, Depends(get_conversation_service)
]
SberIdServiceDep = Annotated[SberIdService, Depends(get_sberid_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
RAGServiceDep = Annotated[RAGService, Depends(get_rag_service)]
RegionServiceDep = Annotated[RegionService, Depends(get_region_service)]
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
