from dataclasses import dataclass


@dataclass(slots=True)
class MemoryExtraction:
    region: str | None = None
    memory: str | None = None

    @property
    def has_updates(self) -> bool:
        return self.region is not None or self.memory is not None
