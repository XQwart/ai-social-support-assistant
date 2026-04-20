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

    def import_from_data(
        self,
        sources: list[dict],
    ) -> dict:

        total_processed_pages = 0
        total_found_links = 0
        total_unique_found = 0
        total_created_links = 0
        total_skipped_existing = 0

        for item in sources:
            region_name_raw = item.get("region")
            region_code_raw = item.get("code")
            source_items = item.get("sources", [])

            region = None
            region_name = None
            region_code = None

            if region_name_raw is not None and region_code_raw is not None:
                region_name = str(region_name_raw).strip()
                region_code = str(region_code_raw).strip().zfill(2)

                if region_name and region_code:
                    region = self._region_service.get_or_create(
                        code=region_code,
                        name=region_name,
                    )

            if region is not None:
                logger.info(
                    "Обработка региона %s (%s)",
                    region_name,
                    region_code,
                )
            else:
                logger.info(
                    "Обработка глобальных источников",
                )

            for source_item in source_items:
                url = source_item["url"]
                place_of_work = source_item.get("place_of_work", None)

                if region is not None:
                    root_source = (
                        self._source_registration_service.register_source_for_region(
                            url=url,
                            region_id=region.id,
                            name=region_name,
                            place_of_work=place_of_work,
                        )
                    )
                else:
                    logger.info(place_of_work)
                    root_source = (
                        self._source_registration_service.get_or_create_source(
                            url=url, name=None, place_of_work=place_of_work
                        )
                    )

                discovery_result = (
                    self._link_discovery_service.discover_and_store_links(
                        root_source=root_source,
                        max_depth=self._max_depth,
                        max_pages=self._max_pages,
                    )
                )

                total_processed_pages += discovery_result["processed_pages"]
                total_found_links += discovery_result["total_found"]
                total_unique_found += discovery_result["unique_found"]
                total_created_links += discovery_result["created"]
                total_skipped_existing += discovery_result["skipped_existing"]

        result = {
            "sources_processed": len(sources),
            "processed_pages": total_processed_pages,
            "found_links": total_found_links,
            "unique_found_links": total_unique_found,
            "created_discovered_sources": total_created_links,
            "skipped_existing_discovered_sources": total_skipped_existing,
            "max_depth": self._max_depth,
        }

        logger.info("Импорт регионов и source завершён: %s", result)
        return result
