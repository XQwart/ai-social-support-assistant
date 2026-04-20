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
    address_reg: dict | None = None
    address_of_actual_residence: dict | None = None

    @property
    def region_reg(self) -> str | None:
        return self._get_region(self.address_reg)

    @property
    def region_current(self) -> str | None:
        return self._get_region(self.address_of_actual_residence)

    def _get_region(self, address: dict | None) -> str | None:
        if address is None:
            return None

        region = address["region"]

        return region if region else None


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
