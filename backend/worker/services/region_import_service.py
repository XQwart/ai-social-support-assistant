from __future__ import annotations

import logging

from worker.services.discovery_service import LinkDiscoveryService
from worker.services.source.region_service import RegionService
from worker.services.source.source_registration_service import SourceRegistrationService

logger = logging.getLogger(__name__)


class RegionSourceImportService:
    def __init__(
        self,
        region_service: RegionService,
        source_registration_service: SourceRegistrationService,
        link_discovery_service: LinkDiscoveryService,
        max_depth: int = 0,
        max_pages: int = 30,
    ) -> None:
        self._max_depth = max_depth
        self._max_pages = max_pages
        self._region_service = region_service
        self._source_registration_service = source_registration_service
        self._link_discovery_service = link_discovery_service

    async def import_one_source(
        self,
        url: str,
        region_name: str | None,
        region_code: str | None,
        place_of_work: str | None,
    ) -> dict:
        region = None

        if region_name and region_code:
            region = await self._region_service.get_or_create(
                code=region_code,
                name=region_name,
            )

        if region is not None:
            logger.info(
                "Обработка региона %s (%s), source=%s",
                region_name,
                region_code,
                url,
            )
            root_source = (
                await self._source_registration_service.register_source_for_region(
                    url=url,
                    region_id=region.id,
                    name=region_name,
                    place_of_work=place_of_work,
                )
            )
        else:
            logger.info("Обработка глобального source=%s", url)
            root_source = await self._source_registration_service.get_or_create_source(
                url=url,
                name=None,
                place_of_work=place_of_work,
            )

        discovery_result = await self._link_discovery_service.discover_and_store_links(
            root_source=root_source,
            max_depth=self._max_depth,
            max_pages=self._max_pages,
        )

        result = {
            "url": url,
            "region_name": region_name,
            "region_code": region_code,
            "processed_pages": discovery_result["processed_pages"],
            "found_links": discovery_result["total_found"],
            "unique_found_links": discovery_result["unique_found"],
            "created_discovered_sources": discovery_result["created"],
            "skipped_existing_discovered_sources": discovery_result["skipped_existing"],
            "max_depth": self._max_depth,
        }

        logger.info("Импорт source завершён: %s", result)
        return result

    def aggregate_results(self, results: list[dict]) -> dict:
        total_processed_pages = 0
        total_found_links = 0
        total_unique_found = 0
        total_created_links = 0
        total_skipped_existing = 0

        for item in results:
            total_processed_pages += item.get("processed_pages", 0)
            total_found_links += item.get("found_links", 0)
            total_unique_found += item.get("unique_found_links", 0)
            total_created_links += item.get("created_discovered_sources", 0)
            total_skipped_existing += item.get("skipped_existing_discovered_sources", 0)

        result = {
            "sources_processed": len(results),
            "processed_pages": total_processed_pages,
            "found_links": total_found_links,
            "unique_found_links": total_unique_found,
            "created_discovered_sources": total_created_links,
            "skipped_existing_discovered_sources": total_skipped_existing,
            "max_depth": self._max_depth,
        }

        logger.info("Импорт регионов и source завершён: %s", result)
        return result
