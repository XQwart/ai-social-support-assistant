import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from app.dependencies.chat import OwnerChatDep
from app.dependencies.services import MessageServiceDep, ConversationServiceDep
from app.schemas.message_schemas import (
    ChatMessageResponse,
    MessageCreate,
    MessageOut,
    MessageWithChatIdOut,
    SendMessageResponse,
)
from app.schemas.stream_events import StreamEvent, StreamEventType
from app.services.conversation_service import ConversationService
from app.models import ChatModel


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/chats", tags=["Messages"])


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

    return ChatMessageResponse(
        chat_id=chat.id, messages=[MessageOut.model_validate(m) for m in messages]
    )


@router.delete("/{chat_id}/messages/from/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_messages_from(
    chat: OwnerChatDep,
    message_service: MessageServiceDep,
    message_id: int,
) -> None:
    await message_service.delete_messages_from(chat_id=chat.id, message_id=int(message_id))


@router.post("/{chat_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    chat: OwnerChatDep,
    conversation_service: ConversationServiceDep,
    message: MessageCreate,
) -> SendMessageResponse:
    result = await conversation_service.send_message(
        chat=chat, content=message.content, personality=message.personality
    )

    return SendMessageResponse(
        user_message=MessageWithChatIdOut.model_validate(result.user_message),
        assistant_message=MessageWithChatIdOut.model_validate(result.assistant_message),
    )


@router.post("/{chat_id}/messages/stream")
async def stream_message(
    chat: OwnerChatDep,
    conversation_service: ConversationServiceDep,
    message: MessageCreate,
) -> StreamingResponse:
    generator = _stream_ndjson(conversation_service, chat, message.content, message.personality)

    return StreamingResponse(
        generator,
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _stream_ndjson(
    conversation_service: ConversationService,
    chat: ChatModel,
    content: str,
    personality: str = "default",
) -> AsyncIterator[bytes]:
    try:
        async for event in conversation_service.send_message_stream(
            chat=chat, content=content, personality=personality
        ):
            yield _serialize_event(event)
    except Exception:
        logger.exception("Failed to stream conversation")
        yield _serialize_event(
            {"type": StreamEventType.ERROR.value, "detail": "Internal error"}
        )


def _serialize_event(event: StreamEvent) -> bytes:
    return (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")
