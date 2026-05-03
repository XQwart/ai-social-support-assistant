from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.page_fetch_schemas import FetchErrorKind


class FetchAbortedError(Exception):
    kind: FetchErrorKind

    def __init__(self, detail: str, kind: FetchErrorKind) -> None:
        super().__init__(detail)
        self.kind = kind


class ContentParsingError(Exception):
    kind: FetchErrorKind

    def __init__(self, detail: str, kind: FetchErrorKind) -> None:
        super().__init__(detail)
        self.kind = kind


class UrlSafetyError(Exception):
    pass
