from fastapi import APIRouter, Query, status

from app.dependencies.chat import OwnerChatDep
from app.dependencies.services import MessageServiceDep, ChatServiceDep
from app.dependencies.ai import AIServiceDep
from app.schemas.message import (
    ChatMessageResponse,
    MessageCreate,
    SendMessageResponse,
)
from app.models.message import MessageRole


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
    chat: OwnerChatDep,
    message_service: MessageServiceDep,
    chat_service: ChatServiceDep,
    ai_service: AIServiceDep,
    message: MessageCreate,
) -> SendMessageResponse:
    user_msg = await message_service.send_message(
        chat_id=chat.id, message=message.content, role=MessageRole.USER
    )

    all_messages = await message_service.get_all_messages(
        chat_id=chat.id, limit=1000, offset=0
    )

    compressed_context = None
    context_compressed_notification = False

    non_system_msgs = [m for m in all_messages if m.role != MessageRole.SYSTEM]
    system_msgs = [m for m in all_messages if m.role == MessageRole.SYSTEM]

    if len(non_system_msgs) > 10:
        existing_summary = system_msgs[-1].content if system_msgs else None

        if len(non_system_msgs) % 10 <= 1:
            msgs_to_compress = [
                {"role": m.role.value, "content": m.content}
                for m in non_system_msgs[:-1]
            ]
            compressed_context = await ai_service.compress_context(msgs_to_compress)

            await message_service.send_message(
                chat_id=chat.id,
                message=compressed_context,
                role=MessageRole.SYSTEM,
            )
            context_compressed_notification = True
            chat_history: list[dict[str, str]] = []
        else:
            compressed_context = existing_summary
            recent_start = max(0, len(non_system_msgs) - 11)
            chat_history = [
                {"role": m.role.value, "content": m.content}
                for m in non_system_msgs[recent_start:-1]
            ]
    else:
        chat_history = [
            {"role": m.role.value, "content": m.content}
            for m in non_system_msgs[:-1]
        ]

    ai_response = await ai_service.generate_response(
        user_message=message.content,
        chat_history=chat_history,
        compressed_context=compressed_context,
    )

    assistant_msg = await message_service.send_message(
        chat_id=chat.id, message=ai_response, role=MessageRole.ASSISTANT
    )

    await chat_service.update_chat(chat.id)

    return SendMessageResponse(
        user_message=user_msg,
        assistant_message=assistant_msg,
        context_compressed=context_compressed_notification,
    )
