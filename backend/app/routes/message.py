from fastapi import APIRouter, Query, status

from app.dependencies.chat import OwnerChatDep
from app.dependencies.services import MessageServiceDep, ConversationServiceDep
from app.schemas.message import (
    ChatMessageResponse,
    MessageCreate,
    SendMessageResponse,
)


router = APIRouter(prefix="/chats")


@router.get("/{chat_id}/messages", status_code=status.HTTP_200_OK)
async def get_all_chat_messages(
    chat: OwnerChatDep,
    message_service: MessageServiceDep,
    limit: int = Query(100),
    offset: int = Query(0),
) -> ChatMessageResponse:
    messages = await message_service.get_messages(
        chat_id=chat.id, limit=limit, offset=offset
    )

    return ChatMessageResponse(chat_id=chat.id, messages=messages)


@router.post("/{chat_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    chat: OwnerChatDep,
    conversation_service: ConversationServiceDep,
    message: MessageCreate,
) -> SendMessageResponse:

    user_msg, assistant_msg, was_compressed = await conversation_service.send_message(
        chat=chat, content=message.content
    )

    return SendMessageResponse(
        user_message=user_msg,
        assistant_message=assistant_msg,
        context_compressed=was_compressed,
    )
