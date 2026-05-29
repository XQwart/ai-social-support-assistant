from __future__ import annotations

from enum import Enum
from typing import Any, Literal


class StreamEventType(str, Enum):
    USER_MESSAGE = "user_message"
    PHASE_START = "phase_start"
    TOKEN = "token"
    PHASE_END = "phase_end"
    ACTION_START = "action_start"
    ACTION_END = "action_end"
    ASSISTANT_MESSAGE = "assistant_message"
    DONE = "done"
    ERROR = "error"


class StreamActionKind(str, Enum):
    RAG = "rag"
    WEB_SEARCH = "web_search"
    FETCH_PAGE = "fetch_page"
    MEMORY = "memory"
    OTHER = "other"


PhaseRole = Literal["thinking", "final"]


TOOL_TO_KIND: dict[str, StreamActionKind] = {
    "search_knowledge_base": StreamActionKind.RAG,
    "search_web": StreamActionKind.WEB_SEARCH,
    "fetch_page": StreamActionKind.FETCH_PAGE,
    "save_user_facts": StreamActionKind.MEMORY,
}


def tool_kind(tool_name: str) -> StreamActionKind:
    return TOOL_TO_KIND.get(tool_name, StreamActionKind.OTHER)


StreamEvent = dict[str, Any]
