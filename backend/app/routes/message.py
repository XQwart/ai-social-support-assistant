from fastapi import APIRouter, Query, status

from app.dependencies.chat import OwnerChatDep
from app.dependencies.services import MessageServiceDep
from app.schemas.message import ChatMessageResponse, MessageCreate, MessageWithChatIdOut

router = APIRouter(prefix="/chats")


@router.get("/{chat_id}/messages", status_code=status.HTTP_200_OK)
async def get_all_chat_messages(
    chat: OwnerChatDep,
    message_service: MessageServiceDep,
    limit: int = Query(100),
    offset: int = Query(0),
) -> ChatMessageResponse:
    messages = await message_service.get_all_messages(
        chat_id=chat.id, limit=limit, offset=offset
    )

    return ChatMessageResponse(chat_id=chat.id, messages=messages)


@router.post("/{chat_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    chat: OwnerChatDep, message_service: MessageServiceDep, message: MessageCreate
) -> MessageWithChatIdOut:
    new_message = await message_service.send_message(
        chat_id=chat.id, message=message.content
    )

    # TODO: Добавить обновление поля updated_at в чате

    return MessageWithChatIdOut(new_message)
