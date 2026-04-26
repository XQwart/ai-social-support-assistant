from __future__ import annotations

import logging
from collections import deque

from worker.models.source import Source
from worker.services.parsing.link_extractor import DiscoveredLink, HtmlLinkExtractor
from worker.services.parsing.web_fetcher import WebPageFetcher
from worker.services.source.source_registration_service import SourceRegistrationService

logger = logging.getLogger(__name__)


class LinkDiscoveryService:
    def __init__(
        self,
        fetcher: WebPageFetcher,
        link_extractor: HtmlLinkExtractor,
        source_registration_service: SourceRegistrationService,
    ) -> None:
        self._fetcher = fetcher
        self._link_extractor = link_extractor
        self._source_registration_service = source_registration_service

    async def discover_and_store_links(
        self,
        root_source: Source,
        max_depth: int,
        max_pages: int,
    ) -> dict:
        if root_source.document_type != "html":
            return {
                "source_id": root_source.id,
                "processed_pages": 1,
                "visited_urls": 1,
                "total_found": 0,
                "unique_found": 0,
                "created": 0,
                "skipped_existing": 0,
                "max_depth": max_depth,
            }

        visited: set[str] = set()
        queued: set[str] = {root_source.url}
        queue = deque([(root_source.url, 0)])

        total_found = 0
        total_unique_found = 0
        total_created = 0
        processed_pages = 0

        while queue:
            current_url, depth = queue.popleft()

            if current_url in visited:
                continue

            if processed_pages >= max_pages:
                logger.info(
                    "Source %s: достигнут лимит max_pages=%s",
                    root_source.id,
                    max_pages,
                )
                break

            visited.add(current_url)

            html = await self._fetcher.get_html_fast(current_url)
            if not html:
                continue

            processed_pages += 1

            links = self._link_extractor.extract_links(
                source_id=root_source.id,
                html=html,
                base_url=current_url,
                depth=depth + 1,
            )

            if not links:
                continue

            total_found += len(links)

            unique_links = self._deduplicate_links(links)
            total_unique_found += len(unique_links)

            created_sources = (
                await self._source_registration_service.register_discovered_sources(
                    links=unique_links,
                    place_of_work=root_source.place_of_work,
                )
            )
            total_created += len(created_sources)

            if depth >= max_depth:
                continue

            for link in unique_links:
                if link.document_type != "html":
                    continue

                if link.url not in visited and link.url not in queued:
                    queue.append((link.url, depth + 1))
                    queued.add(link.url)

        result = {
            "source_id": root_source.id,
            "processed_pages": processed_pages,
            "visited_urls": len(visited),
            "total_found": total_found,
            "unique_found": total_unique_found,
            "created": total_created,
            "skipped_existing": total_unique_found - total_created,
            "max_depth": max_depth,
        }

        logger.info(
            "Source %s: обработано страниц=%s, найдено ссылок=%s, уникальных=%s, создано=%s, пропущено=%s, max_depth=%s",
            root_source.id,
            result["processed_pages"],
            result["total_found"],
            result["unique_found"],
            result["created"],
            result["skipped_existing"],
            result["max_depth"],
        )

        return result

    @staticmethod
    def _deduplicate_links(links: list[DiscoveredLink]) -> list[DiscoveredLink]:
         unique_links_map: dict[str, DiscoveredLink] = {}

        for link in links:
            unique_links_map.setdefault(link.url, link)

        return sorted(
            unique_links_map.values(),
            key=lambda link: link.url,
        )