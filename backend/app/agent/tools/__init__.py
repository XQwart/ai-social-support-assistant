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
    from app.services.agent import AgentToolsScopeFactory


logger = logging.getLogger(__name__)


def create_user_tools(
    user: UserModel,
    scope_factory: AgentToolsScopeFactory,
    config: Config,
) -> list[BaseTool]:
    memory_tool = make_memory_tool(user, scope_factory)
    rag_tool = make_retrive_tool(user, scope_factory, config)
    web_search_tool = make_search_web_tool(scope_factory.web_search_service, config)
    fetch_page_tool = make_page_fetch_tool(scope_factory.page_fetch_service, config)

    return [memory_tool, rag_tool, web_search_tool, fetch_page_tool]
