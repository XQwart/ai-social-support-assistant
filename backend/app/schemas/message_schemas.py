from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.message_model import MessageRole, MessageModel


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageWithChatIdOut(MessageOut):
    chat_id: int


class ChatMessageResponse(BaseModel):
    chat_id: int
    messages: list[MessageOut]


class SendMessageResponse(BaseModel):
    user_message: MessageWithChatIdOut
    assistant_message: MessageWithChatIdOut


@dataclass(slots=False)
class ConversationResult:
    user_message: MessageModel
    assistant_message: MessageModel
