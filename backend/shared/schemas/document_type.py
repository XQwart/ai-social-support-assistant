from enum import Enum


class AccessScope(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"


class GeoScope(str, Enum):
    FEDERAL = "federal"
    REGIONAL = "regional"
