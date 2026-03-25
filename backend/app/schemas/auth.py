from pydantic import BaseModel, ConfigDict


class SberTokenData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    id_token: str
    refresh_token: str | None = None

    model_config = ConfigDict(extra="ignore")


class SberUserInfo(BaseModel):
    sub: str
    given_name: str
    family_name: str


class TokenDataOut(BaseModel):
    user_id: int
