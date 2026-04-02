from __future__ import annotations
from dataclasses import dataclass

from worker.schemas.status import SourceStatus


@dataclass
class ProcessingResult:
    source_id: int
    url: str
    region_code: int
    status: SourceStatus
    chunks_count: int = 0
    vectors_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "url": self.url,
            "region_code": self.region_code,
            "status": self.status.value,
            "chunks_count": self.chunks_count,
            "vectors_count": self.vectors_count,
            "error": self.error,
        }
