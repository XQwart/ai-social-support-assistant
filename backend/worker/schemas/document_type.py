from enum import StrEnum


class AccessScope(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"


class GeoScope(StrEnum):
    FEDERAL = "federal"
    REGIONAL = "regional"
