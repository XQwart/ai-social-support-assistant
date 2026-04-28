"""Unit tests for :class:`admin_service.services.chunk_admin_service.ChunkAdminService`.

The contract under test: every Qdrant point that is upserted as a result
of an admin chunk edit MUST end up persisted as ``chunks.qdrant_point_id``
on the same row, so the next admin edit can target the exact vector.

The tests use lightweight stubs in place of:

- the embedding client,
- the AsyncQdrantClient,
- the AdminChunkRepository,
- the AdminAuditService.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


@dataclass
class _StubSource:
    id: int
    url: str
    name: str | None = None
    place_of_work: str | None = None


@dataclass
class _StubChunk:
    id: int
    source_id: int
    source_url: str
    source_name: str | None
    chunk_index: int
    text: str
    qdrant_point_id: UUID | None


class _StubChunkRepo:
    def __init__(self, source: _StubSource, region_codes: list[str]) -> None:
        self._source = source
        self._region_codes = region_codes
        self._chunks: dict[int, _StubChunk] = {}
        self._next_id = 1

    async def get_source(self, source_id: int) -> _StubSource | None:
        return self._source if source_id == self._source.id else None

    async def get_source_region_codes(self, source_id: int) -> list[str]:
        return list(self._region_codes)

    async def next_chunk_index(self, source_id: int) -> int:
        return len(
            [c for c in self._chunks.values() if c.source_id == source_id]
        )

    async def create(
        self,
        *,
        source_id: int,
        source_url: str,
        source_name: str | None,
        chunk_index: int,
        text: str,
        qdrant_point_id: UUID,
    ) -> _StubChunk:
        chunk = _StubChunk(
            id=self._next_id,
            source_id=source_id,
            source_url=source_url,
            source_name=source_name,
            chunk_index=chunk_index,
            text=text,
            qdrant_point_id=qdrant_point_id,
        )
        self._chunks[chunk.id] = chunk
        self._next_id += 1
        return chunk

    async def update_text_and_point_id(
        self,
        *,
        chunk_id: int,
        text: str,
        qdrant_point_id: UUID,
    ) -> None:
        chunk = self._chunks[chunk_id]
        chunk.text = text
        chunk.qdrant_point_id = qdrant_point_id

    async def get_by_id(self, chunk_id: int) -> _StubChunk | None:
        return self._chunks.get(chunk_id)

    async def delete(self, chunk_id: int) -> None:
        self._chunks.pop(chunk_id, None)


@dataclass
class _UpsertCall:
    point_id: str
    vector: list[float]
    payload: dict[str, Any]


@dataclass
class _DeleteCall:
    points: list[str]


class _StubQdrant:
    def __init__(self) -> None:
        self.upserts: list[_UpsertCall] = []
        self.deletes: list[_DeleteCall] = []
        self.fail_upsert: bool = False

    async def upsert(self, *, collection_name: str, points: list[Any]) -> None:
        if self.fail_upsert:
            raise RuntimeError("simulated qdrant outage")
        for point in points:
            self.upserts.append(
                _UpsertCall(
                    point_id=str(point.id),
                    vector=list(point.vector),
                    payload=dict(point.payload),
                )
            )

    async def delete(self, *, collection_name: str, points_selector: Any) -> None:
        # PointIdsList exposes ``points`` as a sequence of ids.
        ids = list(points_selector.points)
        self.deletes.append(_DeleteCall(points=[str(i) for i in ids]))


class _StubEmbedding:
    def __init__(self, vector: list[float] | None = None) -> None:
        self.vector = vector or [0.1, 0.2, 0.3, 0.4]
        self.calls: list[list[str]] = []

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [self.vector for _ in texts]


@dataclass
class _AuditEntry:
    action: str
    admin_id: int
    target_type: str
    target_id: str | None
    payload_diff: dict[str, Any]


class _StubAudit:
    def __init__(self) -> None:
        self.entries: list[_AuditEntry] = []

    async def record(
        self,
        *,
        action: str,
        admin_id: int | None,
        target_type: str | None,
        target_id: str | None,
        payload_diff: dict[str, Any] | None,
    ) -> None:
        self.entries.append(
            _AuditEntry(
                action=action,
                admin_id=int(admin_id or 0),
                target_type=str(target_type or ""),
                target_id=target_id,
                payload_diff=dict(payload_diff or {}),
            )
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_source() -> _StubSource:
    return _StubSource(
        id=42,
        url="https://example.com/page",
        name="Example",
        place_of_work="HQ",
    )


@pytest.fixture
def service(stub_source):
    from admin_service.services.chunk_admin_service import ChunkAdminService

    repo = _StubChunkRepo(source=stub_source, region_codes=["77", "78"])
    qdrant = _StubQdrant()
    embedding = _StubEmbedding()
    audit = _StubAudit()
    svc = ChunkAdminService(
        repo=repo,
        qdrant=qdrant,
        embedding=embedding,
        audit=audit,
        collection="chunks",
    )
    return svc, repo, qdrant, embedding, audit


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_persists_uuid_and_does_two_pass_upsert(
    service, stub_source
):
    svc, repo, qdrant, embedding, audit = service

    chunk = await svc.create(
        source_id=stub_source.id,
        text="  hello world  ",
        admin_id=7,
    )

    # Embedding was called once, with the trimmed text.
    assert embedding.calls == [["hello world"]]

    # Qdrant got two upserts for the same point id (the round-trip pattern).
    assert len(qdrant.upserts) == 2
    point_ids = {call.point_id for call in qdrant.upserts}
    assert len(point_ids) == 1
    point_id_str = next(iter(point_ids))

    # The first pass had text_id=None (chunk.id wasn't known yet); the
    # second pass had text_id == chunk.id.
    assert qdrant.upserts[0].payload["text_id"] is None
    assert qdrant.upserts[1].payload["text_id"] == chunk.id

    # The chunk row keeps the same UUID as the point.
    assert chunk.qdrant_point_id is not None
    assert str(chunk.qdrant_point_id) == point_id_str

    # Region/place metadata was forwarded into the payload.
    assert qdrant.upserts[0].payload["region_codes"] == ["77", "78"]
    assert qdrant.upserts[0].payload["place_of_work"] == "HQ"
    assert qdrant.upserts[0].payload["source_id"] == stub_source.id
    assert qdrant.upserts[0].payload["chunk_index"] == 0


@pytest.mark.asyncio
async def test_update_reuses_existing_point_id(service, stub_source):
    svc, repo, qdrant, embedding, audit = service

    existing_uuid = uuid4()
    repo._chunks[1] = _StubChunk(
        id=1,
        source_id=stub_source.id,
        source_url=stub_source.url,
        source_name=stub_source.name,
        chunk_index=0,
        text="old",
        qdrant_point_id=existing_uuid,
    )
    repo._next_id = 2

    refreshed = await svc.update(chunk_id=1, text="new text", admin_id=9)

    # Only one upsert (no two-pass needed since chunk.id already exists).
    assert len(qdrant.upserts) == 1
    call = qdrant.upserts[0]
    assert call.point_id == str(existing_uuid)
    assert call.payload["text_id"] == 1

    # PG row still carries the same UUID.
    assert refreshed.qdrant_point_id == existing_uuid
    assert refreshed.text == "new text"


@pytest.mark.asyncio
async def test_update_assigns_uuid_when_chunk_lacks_one(
    service, stub_source
):
    svc, repo, qdrant, embedding, audit = service

    repo._chunks[1] = _StubChunk(
        id=1,
        source_id=stub_source.id,
        source_url=stub_source.url,
        source_name=stub_source.name,
        chunk_index=0,
        text="legacy",
        qdrant_point_id=None,
    )
    repo._next_id = 2

    refreshed = await svc.update(chunk_id=1, text="filled in", admin_id=9)

    assert len(qdrant.upserts) == 1
    upserted_id = qdrant.upserts[0].point_id

    assert refreshed.qdrant_point_id is not None
    assert str(refreshed.qdrant_point_id) == upserted_id


@pytest.mark.asyncio
async def test_delete_removes_qdrant_point_then_pg_row(service, stub_source):
    svc, repo, qdrant, embedding, audit = service

    point_id = uuid4()
    repo._chunks[1] = _StubChunk(
        id=1,
        source_id=stub_source.id,
        source_url=stub_source.url,
        source_name=stub_source.name,
        chunk_index=0,
        text="bye",
        qdrant_point_id=point_id,
    )

    await svc.delete(chunk_id=1, admin_id=7)

    assert qdrant.deletes == [_DeleteCall(points=[str(point_id)])]
    assert 1 not in repo._chunks


@pytest.mark.asyncio
async def test_create_propagates_qdrant_failure_as_persistence_error(
    service, stub_source
):
    from admin_service.services.chunk_admin_service import (
        ChunkPersistenceError,
    )

    svc, repo, qdrant, embedding, audit = service
    qdrant.fail_upsert = True

    with pytest.raises(ChunkPersistenceError):
        await svc.create(
            source_id=stub_source.id,
            text="payload",
            admin_id=1,
        )

    # Nothing was written to PG when Qdrant failed on the first pass.
    assert repo._chunks == {}


@pytest.mark.asyncio
async def test_create_rejects_blank_text(service, stub_source):
    from admin_service.services.chunk_admin_service import (
        ChunkValidationError,
    )

    svc, _, _, _, _ = service

    with pytest.raises(ChunkValidationError):
        await svc.create(source_id=stub_source.id, text="   ", admin_id=1)
