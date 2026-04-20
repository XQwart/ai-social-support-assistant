from dataclasses import dataclass


@dataclass(slots=True)
class RetrievedChunk:
    source_name: str | None
    source_url: str
    text: str
    is_internal: bool
