from dataclasses import dataclass
from enum import Enum, auto


class FetchErrorKind(str, Enum):
    BLOCKED = auto()
    HTTP_STATUS = auto()
    TOO_LARGE = auto()
    UNEXPECTED = auto()
    UNSUPPORTED_TYPE = auto()
    EMPTY_CONTENT = auto()
    NETWORK = auto()
    PARSE_ERROR = auto()


@dataclass(slots=True)
class FetchResult:
    url: str
    title: str = ""
    content: str = ""
    error_kind: FetchErrorKind | None = None
    error_detail: str = ""

    @property
    def has_error(self) -> bool:
        return self.error_kind is not None
