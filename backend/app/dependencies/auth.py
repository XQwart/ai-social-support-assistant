from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import TokenDataOut
from .jwt import AccessTokenDep

_security = HTTPBearer()


async def validate_token(
    access_token_util: AccessTokenDep,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
) -> TokenDataOut:
    token = creds.credentials

    payload = access_token_util.validate(token)
    if not payload:
        raise HTTPException(401, "Unauthorized")

    return TokenDataOut(**payload)


AuthDep = Annotated[TokenDataOut, Depends(validate_token)]
