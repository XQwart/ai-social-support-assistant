from pydantic import BaseModel


class SberTokenData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    id_token: str
    refresh_token: str


class SberUserInfo(BaseModel):
    sub: str
    given_name: str | None = None
    family_name: str | None = None
