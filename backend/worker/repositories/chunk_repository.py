from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from worker.models.chunk import DocumentChunk
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
