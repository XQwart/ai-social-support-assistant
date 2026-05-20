from typing import Annotated

from fastapi import Depends, Request

from app.utils.jwt_utils import JWTTokenUtil
from shared.utils.pdf_extractor import PdfTextExtractor
from app.dependencies.config import ConfigDep

_pdf_extractor = PdfTextExtractor()


def get_access_token_util(config: ConfigDep) -> JWTTokenUtil:
    return JWTTokenUtil(
        ttl=config.jwt_access_token_expire,
        secret=config.jwt_access_secret,
    )


def get_refresh_token_util(config: ConfigDep) -> JWTTokenUtil:
    return JWTTokenUtil(
        ttl=config.jwt_refresh_token_expire,
        secret=config.jwt_refresh_secret,
    )


def get_pdf_extractor(request: Request) -> PdfTextExtractor:
    return request.app.state.pdf_extractor


AccessTokenDep = Annotated[JWTTokenUtil, Depends(get_access_token_util)]
RefreshTokenDep = Annotated[JWTTokenUtil, Depends(get_refresh_token_util)]

PDFExtractorDep = Annotated[PdfTextExtractor, Depends(get_pdf_extractor)]
