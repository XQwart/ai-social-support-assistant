from datetime import datetime
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


class ChatResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatUpdateRequest(BaseModel):
    title: str


class ChatsPageResponse(BaseModel):
    items: list[ChatResponse]
    total: int
    limit: int
    offset: int


@dataclass(slots=True)
class ChatContextStats:
    last_total_tokens: int
    reserve_input_tokens: int
    recent_input_deltas: list[int]
