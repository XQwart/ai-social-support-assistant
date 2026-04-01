from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: int
    first_name: str | None
    second_name: str | None
    place_of_work: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
