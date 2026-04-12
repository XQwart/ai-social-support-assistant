from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from .user_schemas import UserOut


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
    place_of_work: str | None = None


class AuthResponse(BaseModel):
    message: str | None = None
    token: str
    user: UserOut


class SberParamsResponse(BaseModel):
    client_id: str
    authorize_url: str
    redirect_uri: str
    scopes: str
    name: str
    response_type: str
    state: str
    nonce: str


class TokenDataOut(BaseModel):
    user_id: int


@dataclass(slots=True)
class SberCallbackResult:
    login_code: str
    redirect_url: str | None


@dataclass(slots=True)
class AuthTokenPair:
    access_token: str
    refresh_token: str
