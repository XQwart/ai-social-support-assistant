from __future__ import annotations

from worker.models.source import Source
from worker.services.parsing.link_extractor import DiscoveredLink
from worker.repositories.source_reg_repository import SourceRegistrationRepository
from worker.utils.document_type import detect_document_type


class SourceRegistrationService:
    def __init__(
        self,
        source_repository: SourceRegistrationRepository,
    ) -> None:
        self._source_repository = source_repository

    def get_by_url(self, url: str) -> Source | None:
        return self._source_repository.get_by_url(url)

    def get_or_create_source(
        self,
        url: str,
        place_of_work: str | None,
        name: str | None = None,
    ) -> Source:
        source = self._source_repository.get_by_url(url)
        print(f"нашли соурс с {place_of_work}")
        if source is not None:
            return source

        document_type = detect_document_type(url)
        print(place_of_work)
        return self._source_repository.create_source(
            url=url, name=name, document_type=document_type, place_of_work=place_of_work
        )

    def get_region_codes_by_source_id(self, source_id: int) -> list[str]:
        return self._source_repository.get_region_codes_by_source_id(source_id)

    def register_source_for_region(
        self,
        url: str,
        region_id: int,
        name: str | None = None,
        place_of_work: str | None = None,
    ) -> Source:
        source = self.get_or_create_source(
            url=url, name=name, place_of_work=place_of_work
        )

        self._source_repository.add_region_to_source(
            source_id=source.id,
            region_id=region_id,
        )
        return source

    def register_discovered_sources(
        self, links: list[DiscoveredLink], place_of_work: str | None = None
    ) -> list[Source]:
        if not links:
            return []

        urls = [link.url for link in links]
        existing_urls = self._source_repository.get_existing_urls(urls)
        created_sources: list[Source] = []
        for link in links:
            if link.url in existing_urls:
                continue

            source = self._source_repository.create_source(
                url=link.url,
                name=None,
                document_type=link.document_type,
                place_of_work=place_of_work,
            )
            created_sources.append(source)

        return created_sources
