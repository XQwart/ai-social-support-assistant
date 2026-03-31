from fastapi import APIRouter, Query, status

from app.dependencies.chat import OwnerChatDep
from app.dependencies.auth import AuthDep
from app.dependencies.services import ChatServiceDep
from app.exceptions.base_exceptions import NotFoundError
from app.schemas.chat_schemas import ChatResponse, ChatsPageResponse
from app.schemas.message_schemas import MessageCreate


router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_chat(
    token_data: AuthDep, chat_service: ChatServiceDep, message: MessageCreate
) -> ChatResponse:
    chat = await chat_service.create_chat(token_data.user_id, message=message.content)

    return ChatResponse.model_validate(chat)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_chats(
    token_data: AuthDep,
    chat_service: ChatServiceDep,
    limit: int = Query(100),
    offset: int = Query(0),
) -> ChatsPageResponse:
    chats, total = await chat_service.get_chats(
        user_id=token_data.user_id,
        limit=limit,
        offset=offset,
    )

    return ChatsPageResponse(
        items=[ChatResponse.model_validate(m) for m in chats],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{chat_id}", status_code=status.HTTP_200_OK)
async def get_chat_info(chat: OwnerChatDep) -> ChatResponse:
    return ChatResponse.model_validate(chat)


@router.delete("/{chat_id}")
async def delete_chat(
    chat: OwnerChatDep,
    chat_service: ChatServiceDep,
) -> None:
    success = await chat_service.delete_chat(chat_id=chat.id)

    if not success:
        raise NotFoundError("Chat not found")
