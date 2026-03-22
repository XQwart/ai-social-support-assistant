from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.message import MessageRole


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: MessageRole
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
