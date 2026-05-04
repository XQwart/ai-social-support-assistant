from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from langchain.tools import BaseTool

from .memory_tool import make_memory_tool
from .rag_tool import make_retrive_tool
from .web_search_tool import make_search_web_tool
from .fetch_page_tool import make_page_fetch_tool

if TYPE_CHECKING:
    from app.core.config import Config
    from app.models import UserModel
    from app.services import (
        RegionService,
        RAGService,
        UserService,
        WebSearchService,
        PageFetchService,
    )


logger = logging.getLogger(__name__)


def create_user_tools(
    user: UserModel,
    user_service: UserService,
    rag_service: RAGService,
    region_service: RegionService,
    web_search_service: WebSearchService,
    page_fetch_service: PageFetchService,
    config: Config,
) -> list[BaseTool]:
    memory_tool = make_memory_tool(user, user_service)
    rag_tool = make_retrive_tool(user, rag_service, region_service, config)
    web_search_tool = make_search_web_tool(web_search_service, config)
    fetch_page_tool = make_page_fetch_tool(page_fetch_service, config)

    return [memory_tool, rag_tool, web_search_tool, fetch_page_tool]
