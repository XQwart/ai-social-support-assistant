from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    id: int
    bank_id: str
    first_name: str
    second_name: str


class UserRead(BaseModel):
    id: int
    bank_id: str
    first_name: str
    second_name: str
    created_at: datetime

    model_config = {"from_attributes": True}
