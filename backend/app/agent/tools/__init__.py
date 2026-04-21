from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from langchain.tools import BaseTool

from .memory_tool import make_memory_tool
from .rag_tool import make_retrive_tool

if TYPE_CHECKING:
    from app.models import UserModel
    from app.services import RegionService, RAGService, UserService


logger = logging.getLogger(__name__)


def create_user_tools(
    user: UserModel,
    user_service: UserService,
    rag_service: RAGService,
    region_service: RegionService,
) -> list[BaseTool]:
    memory_tool = make_memory_tool(user, user_service)
    rag_tool = make_retrive_tool(user, rag_service, region_service)

    return [memory_tool, rag_tool]
