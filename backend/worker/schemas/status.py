# worker/schemas/source_status.py
from enum import StrEnum


class SourceStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    SAVING = "saving"
    SUCCESS = "success"
    PARSE_FAILED = "parse_failed"
    EMPTY_CONTENT = "empty_content"
    CHUNK_FAILED = "chunk_failed"
    EMBEDDING_FAILED = "embedding_failed"
    SAVE_FAILED = "save_failed"
