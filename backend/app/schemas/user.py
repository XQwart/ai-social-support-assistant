from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    id: int
    bank_id: str
    first_name: str | None
    second_name: str | None


class UserRead(BaseModel):
    id: int
    bank_id: str
    first_name: str | None
    second_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
