from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ChatResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatsPageResponse(BaseModel):
    items: list[ChatResponse]
    total: int
    limit: int
    offset: int
