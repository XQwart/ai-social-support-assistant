# worker/schemas/source_status.py
from enum import StrEnum


class SourceStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
