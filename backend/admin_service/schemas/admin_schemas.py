from __future__ import annotations

from pydantic import BaseModel, Field


class CreateAdminForm(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=512)
