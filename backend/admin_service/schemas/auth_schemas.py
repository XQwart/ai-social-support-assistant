from __future__ import annotations

from pydantic import BaseModel, Field


class LoginForm(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=512)
    totp: str | None = Field(default=None, max_length=10)


class ChangePasswordForm(BaseModel):
    current_password: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=8, max_length=512)
    confirm_password: str = Field(min_length=8, max_length=512)


class TotpConfirmForm(BaseModel):
    code: str = Field(min_length=6, max_length=10)
