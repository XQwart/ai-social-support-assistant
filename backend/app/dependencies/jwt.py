from typing import Annotated
from datetime import timedelta

from fastapi import Depends

from app.utils.jwt import JWTTokenUtil
from app.dependencies.config import ConfigDep


def get_access_token_util(config: ConfigDep) -> JWTTokenUtil:
    return JWTTokenUtil(
        ttl=timedelta(minutes=config.jwt_access_token_expire),
        secret=config.jwt_access_secret,
    )


def get_refresh_token_util(config: ConfigDep) -> JWTTokenUtil:
    return JWTTokenUtil(
        ttl=timedelta(days=config.jwt_refresh_token_expire),
        secret=config.jwt_refresh_secret,
    )


AccessTokenDep = Annotated[JWTTokenUtil, Depends(get_access_token_util)]
RefreshTokenDep = Annotated[JWTTokenUtil, Depends(get_refresh_token_util)]
