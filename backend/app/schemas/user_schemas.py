from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field

from app.core.constants import is_sber_employee_place_of_work


class UserOut(BaseModel):
    id: int
    first_name: str | None
    second_name: str | None
    place_of_work: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_sber_employee(self) -> bool:
        return is_sber_employee_place_of_work(self.place_of_work)
