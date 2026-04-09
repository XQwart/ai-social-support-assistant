from typing import Annotated
from fastapi import Depends

from app.repositories import (
    ChatRepository,
    MessageRepository,
    OauthRepository,
    TokenRedisRepository,
    UserRepository,
    DocumentRepository,
    ChunkRepository,
)
from app.dependencies.qdrant import QdrantClientDep
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


def get_message_repo(session: DBSessionDep) -> MessageRepository:
    return MessageRepository(session=session)


def get_document_repo(session: DBSessionDep) -> DocumentRepository:
    return DocumentRepository(session)


def get_chunk_repo(client: QdrantClientDep, config: ConfigDep) -> ChunkRepository:
    return ChunkRepository(client, config)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
TokenRedisRepoDep = Annotated[TokenRedisRepository, Depends(get_token_redis_repo)]
OauthRepoDep = Annotated[OauthRepository, Depends(get_auth_redis_repo)]
ChatRepoDep = Annotated[ChatRepository, Depends(get_chat_repo)]
MessageRepoDep = Annotated[MessageRepository, Depends(get_message_repo)]
DocumentRepoDep = Annotated[DocumentRepository, Depends(get_document_repo)]
ChunkRepoDep = Annotated[ChunkRepository, Depends(get_chunk_repo)]
