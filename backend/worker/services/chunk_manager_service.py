from __future__ import annotations


from worker.schemas.document import ParsedDocument
from shared.schemas.document_type import AccessScope, GeoScope
from worker.services.chunk_service import ChunkingService
from worker.services.chunk_index_service import ChunkIndexingService
from worker.services.document_service import DocumentService
from worker.services.source import RegionService, SourceRegistrationService


class ChunkManagementService:
    def __init__(
        self,
        *,
        document_service: DocumentService,
        chunking_service: ChunkingService,
        region_service: RegionService,
        source_service: SourceRegistrationService,
        chunk_indexing_service: ChunkIndexingService,
    ) -> None:
        self._documents = document_service
        self._chunking = chunking_service
        self._regions = region_service
        self._sources = source_service
        self._chunk_indexing = chunk_indexing_service

    async def add_text_to_source(
        self,
        *,
        source_url: str,
        source_name: str | None = None,
        region_code: str | None = None,
        region_name: str | None = None,
        place_of_work: str | None = None,
        text: str,
    ) -> dict:
        text = text.strip()

        if not text:
            return {
                "status": "skipped",
                "reason": "empty text",
            }

        source = await self._get_or_create_source_with_regions(
            source_url=source_url,
            source_name=source_name,
            region_code=region_code,
            region_name=region_name,
            place_of_work=place_of_work,
        )

        document = ParsedDocument(
            source_id=source.id,
            source_url=source.url,
            source_name=source.name,
            text=text,
        )

        return await self.ingest_document(
            document=document,
            replace_existing=False,
        )

    async def ingest_document(
        self,
        *,
        document: ParsedDocument,
        replace_existing: bool,
    ) -> dict:
        chunks = self._chunking.split_document(document=document)

        if not chunks:
            return {
                "source_id": document.source_id,
                "source_url": document.source_url,
                "status": "skipped",
                "reason": "empty chunks",
            }

        chunks_count = len(chunks)

        if replace_existing:
            stored_chunks = await self._documents.save_chunks(
                source_id=document.source_id,
                chunks=chunks,
            )

            await self._documents.delete_index_data_by_source_id(
                source_id=document.source_id,
            )

        else:
            start_chunk_index = await self._documents.get_next_chunk_index(
                source_id=document.source_id,
            )

            for index, chunk in enumerate(chunks):
                chunk.chunk_index = start_chunk_index + index

            stored_chunks = await self._documents.create_chunks(chunks)

        del chunks

        regions = await self._sources.get_region_codes_by_source_id(
            source_id=document.source_id,
        )

        embedded_chunks = await self._chunk_indexing.prepare_index_data(
            stored_chunks=stored_chunks,
        )
        del stored_chunks

        questions_count = sum(len(chunk.questions) for chunk in embedded_chunks)

        access_scope = self._resolve_access_scope(
            place_of_work=document.place_of_work,
        )

        geo_scope = self._resolve_geo_scope(
            region_codes=regions,
        )

        indexed_count = await self._documents.upsert_chunk_vectors(
            chunks=embedded_chunks,
            regions=regions,
            place_of_work=document.place_of_work,
            access_scope=access_scope,
            geo_scope=geo_scope,
        )
        del embedded_chunks

        return {
            "source_id": document.source_id,
            "source_url": document.source_url,
            "status": "success",
            "replace_existing": replace_existing,
            "chunks_count": chunks_count,
            "chunk_vectors_count": indexed_count or 0,
            "questions_count": questions_count,
            "regions": regions,
            "is_global": not regions,
        }

    async def update_chunk(
        self,
        *,
        chunk_id: int,
        text: str,
        place_of_work: str | None = None,
    ) -> dict:
        text = text.strip()

        if not text:
            return {
                "status": "failed",
                "reason": "empty text",
                "chunk_id": chunk_id,
            }

        chunks = await self._documents.get_chunks_by_ids([chunk_id])

        if not chunks:
            return {
                "status": "failed",
                "reason": "chunk not found",
                "chunk_id": chunk_id,
            }

        old_chunk = chunks[0]

        if old_chunk.text == text:
            return {
                "status": "skipped",
                "reason": "text not changed",
                "source_id": old_chunk.source_id,
                "chunk_id": chunk_id,
            }

        await self._documents.delete_index_data_by_chunk_id(chunk_id)

        updated_chunk = await self._documents.update_chunk_text(
            chunk_id=chunk_id,
            text=text,
        )

        regions = await self._sources.get_region_codes_by_source_id(
            source_id=updated_chunk.source_id,
        )

        embedded_chunks = await self._chunk_indexing.prepare_index_data(
            stored_chunks=[updated_chunk],
        )

        access_scope = self._resolve_access_scope(
            place_of_work=place_of_work,
        )

        geo_scope = self._resolve_geo_scope(
            region_codes=regions,
        )

        chunk_vectors_count = await self._documents.upsert_chunk_vectors(
            chunks=embedded_chunks,
            regions=regions,
            place_of_work=place_of_work,
            access_scope=access_scope,
            geo_scope=geo_scope,
        )

        questions_count = sum(len(chunk.questions) for chunk in embedded_chunks)

        del embedded_chunks

        return {
            "status": "success",
            "action": "chunk_updated",
            "source_id": updated_chunk.source_id,
            "chunk_id": updated_chunk.id,
            "regions": regions,
            "is_global": not regions,
            "chunk_vectors_count": chunk_vectors_count or 0,
            "questions_count": questions_count,
        }

    async def delete_chunk(
        self,
        *,
        chunk_id: int,
    ) -> dict:
        chunks = await self._documents.get_chunks_by_ids([chunk_id])

        if not chunks:
            return {
                "status": "skipped",
                "reason": "chunk not found",
                "chunk_id": chunk_id,
            }

        chunk = chunks[0]

        await self._documents.delete_index_data_by_chunk_id(chunk_id)

        deleted_count = await self._documents.delete_chunk_by_id(chunk_id)

        return {
            "status": "success",
            "action": "chunk_deleted",
            "source_id": chunk.source_id,
            "chunk_id": chunk_id,
            "deleted_count": deleted_count,
        }

    async def _get_or_create_source_with_regions(
        self,
        *,
        source_url: str,
        source_name: str | None,
        region_code: str | None,
        region_name: str | None,
        place_of_work: str | None,
    ):
        if region_code is None and region_name is None:
            return await self._sources.get_or_create_source(
                url=source_url,
                name=source_name,
                place_of_work=place_of_work,
            )

        if region_code is not None and region_name is not None:
            region = await self._regions.get_or_create(
                code=region_code,
                name=region_name,
            )

            return await self._sources.register_source_for_region(
                url=source_url,
                region_id=region.id,
                name=source_name,
                place_of_work=place_of_work,
            )

        raise ValueError(
            "region_code and region_name must be both provided or both null"
        )

    def _resolve_access_scope(
        self,
        *,
        place_of_work: str | None,
    ) -> AccessScope:
        if place_of_work:
            return AccessScope.INTERNAL

        return AccessScope.PUBLIC

    def _resolve_geo_scope(
        self,
        *,
        region_codes: list[str],
    ) -> GeoScope:
        if region_codes:
            return GeoScope.REGIONAL

        return GeoScope.FEDERAL
