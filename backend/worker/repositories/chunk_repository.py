from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from shared.models import DocumentChunk
from worker.schemas.document import DocumentChunkCreate, StoredDocumentChunk


class ChunkRepository:
    _session: Session

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_many(
        self,
        chunks: Sequence[DocumentChunkCreate],
    ) -> list[StoredDocumentChunk]:
        if not chunks:
            return []

        rows: list[DocumentChunk] = []

        for chunk in chunks:
            row = DocumentChunk(
                source_id=chunk.source_id,
                source_url=chunk.source_url,
                source_name=chunk.source_name,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
            )
            self._session.add(row)
            rows.append(row)

        self._session.flush()

        return [
            StoredDocumentChunk(
                id=row.id,
                source_id=row.source_id,
                source_url=row.source_url,
                source_name=row.source_name,
                chunk_index=row.chunk_index,
                text=row.text,
            )
            for row in rows
        ]

    def set_qdrant_point_ids(
        self,
        mapping: Mapping[int, str | UUID],
    ) -> int:
        """Persist the mapping ``chunk_id -> qdrant_point_id`` in bulk.

        Returns the number of rows actually updated.
        """

        if not mapping:
            return 0

        updated = 0
        for chunk_id, point_id in mapping.items():
            point_uuid = (
                point_id if isinstance(point_id, UUID) else UUID(str(point_id))
            )
            stmt = (
                update(DocumentChunk)
                .where(DocumentChunk.id == chunk_id)
                .values(qdrant_point_id=point_uuid)
            )
            result = self._session.execute(stmt)
            updated += int(result.rowcount or 0)

        return updated

    def delete_by_source_id(self, source_id: int) -> int:
        stmt = (
            delete(DocumentChunk)
            .where(DocumentChunk.source_id == source_id)
            .returning(DocumentChunk.id)
        )

        result = self._session.execute(stmt)
        deleted_ids = result.scalars().all()
        return len(deleted_ids)

    def get_by_ids(self, chunk_ids: Sequence[int]) -> list[StoredDocumentChunk]:
        if not chunk_ids:
            return []

        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.id.in_(list(chunk_ids)))
            .order_by(DocumentChunk.id.asc())
        )

        rows = list(self._session.scalars(stmt).all())

        return [
            StoredDocumentChunk(
                id=row.id,
                source_id=row.source_id,
                source_url=row.source_url,
                source_name=row.source_name,
                chunk_index=row.chunk_index,
                text=row.text,
            )
            for row in rows
        ]

    def get_by_source_id(self, source_id: int) -> list[StoredDocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.source_id == source_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )

        rows = list(self._session.scalars(stmt).all())

        return [
            StoredDocumentChunk(
                id=row.id,
                source_id=row.source_id,
                source_url=row.source_url,
                source_name=row.source_name,
                chunk_index=row.chunk_index,
                text=row.text,
            )
            for row in rows
        ]
