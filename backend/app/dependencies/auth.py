from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.exceptions.base_exceptions import NotAuthenticatedError
from app.schemas.auth_schemas import TokenDataOut
from .jwt import AccessTokenDep


_security = HTTPBearer()


async def validate_token(
    access_token_util: AccessTokenDep,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
) -> TokenDataOut:
    token = creds.credentials

    payload = access_token_util.validate(token)
    if not payload:
        raise NotAuthenticatedError("Unauthorized")

    return TokenDataOut(user_id=payload["sub"])


AuthDep = Annotated[TokenDataOut, Depends(validate_token)]
