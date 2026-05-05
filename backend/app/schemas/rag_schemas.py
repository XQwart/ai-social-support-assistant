from dataclasses import dataclass


@dataclass(slots=True)
class RetrievedChunk:
    source_name: str | None
    source_url: str | None
    text: str
    is_internal: bool
