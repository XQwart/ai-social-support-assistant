"""Unit tests for :class:`worker.repositories.vector_repository.VectorRepository`.

Verifies the qdrant_point_id round-trip contract:

- ``upsert_chunks`` returns ``{chunk_id: point_id}`` for the chunks it
  actually wrote.
- The point IDs are valid UUIDs (matching what we persist on the
  ``chunks`` table via :meth:`ChunkRepository.set_qdrant_point_ids`).
- Empty input is a no-op (returns an empty mapping, no Qdrant call).
- Chunks with an empty vector are skipped silently and stay out of the
  mapping.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from worker.repositories.vector_repository import VectorRepository
from worker.schemas.document import EmbeddedDocumentChunk


@dataclass
class _UpsertCall:
    collection_name: str
    point_count: int
    point_ids: list[str]


class _StubQdrant:
    def __init__(self) -> None:
        self.upsert_calls: list[_UpsertCall] = []

    def upsert(self, *, collection_name: str, points: list[Any]) -> None:
        self.upsert_calls.append(
            _UpsertCall(
                collection_name=collection_name,
                point_count=len(points),
                point_ids=[str(p.id) for p in points],
            )
        )


def _chunk(chunk_id: int, vector: list[float] | None = None) -> EmbeddedDocumentChunk:
    return EmbeddedDocumentChunk(
        id=chunk_id,
        source_id=1,
        source_url="https://example.com",
        source_name="example",
        chunk_index=chunk_id - 1,
        text=f"chunk {chunk_id}",
        vector=vector if vector is not None else [0.1, 0.2, 0.3],
    )


def test_upsert_chunks_returns_per_chunk_uuid_mapping() -> None:
    qdrant = _StubQdrant()
    repo = VectorRepository(client=qdrant, collection_name="chunks")  # type: ignore[arg-type]

    embedded = [_chunk(1), _chunk(2), _chunk(3)]
    mapping = repo.upsert_chunks(embedded, regions=["77"], place_of_work=None)

    assert set(mapping.keys()) == {1, 2, 3}
    # Every value parses as a UUID.
    for value in mapping.values():
        UUID(value)

    # Mapping values match the IDs Qdrant actually saw.
    assert qdrant.upsert_calls
    written_ids = [pid for call in qdrant.upsert_calls for pid in call.point_ids]
    assert sorted(written_ids) == sorted(mapping.values())


def test_upsert_chunks_empty_input_is_noop() -> None:
    qdrant = _StubQdrant()
    repo = VectorRepository(client=qdrant, collection_name="chunks")  # type: ignore[arg-type]

    mapping = repo.upsert_chunks([], regions=[], place_of_work=None)

    assert mapping == {}
    assert qdrant.upsert_calls == []


def test_upsert_chunks_skips_empty_vectors() -> None:
    qdrant = _StubQdrant()
    repo = VectorRepository(client=qdrant, collection_name="chunks")  # type: ignore[arg-type]

    embedded = [
        _chunk(1, vector=[]),  # skipped
        _chunk(2, vector=[0.1, 0.2]),  # kept
    ]
    mapping = repo.upsert_chunks(embedded, regions=[], place_of_work=None)

    assert list(mapping.keys()) == [2]
    assert qdrant.upsert_calls
    assert qdrant.upsert_calls[0].point_count == 1


def test_upsert_chunks_batches_when_above_batch_size() -> None:
    qdrant = _StubQdrant()
    repo = VectorRepository(
        client=qdrant,  # type: ignore[arg-type]
        collection_name="chunks",
        upsert_batch_size=2,
    )

    embedded = [_chunk(i) for i in range(1, 6)]  # 5 chunks
    mapping = repo.upsert_chunks(embedded, regions=[], place_of_work=None)

    # Five chunks → batches of 2, 2, 1.
    assert [c.point_count for c in qdrant.upsert_calls] == [2, 2, 1]
    assert len(mapping) == 5
