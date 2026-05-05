from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command

logger = logging.getLogger(__name__)


_RAG_TOOL = "search_knowledge_base"
_MEMORY_TOOL = "save_user_facts"
_WEB_SEARCH_TOOL = "search_web"
_FETCH_PAGE_TOOL = "fetch_page"

_LIMIT_MESSAGES = {
    _RAG_TOOL: (
        "Вызов запрещён. Ты уже получил результат "
        "search_knowledge_base в этом ответе — используй его. "
        "Отвечай пользователю на основе уже найденных данных; "
        "если их недостаточно, задай один уточняющий вопрос."
    ),
    _WEB_SEARCH_TOOL: (
        "Вызов запрещён. Ты уже выполнил search_web в этом ответе — "
        "используй полученные результаты. Изменение запроса не делает "
        "вызов новым. Если данных мало — отвечай по тому, что есть, "
        "или честно скажи, что точной информации найти не удалось."
    ),
    _FETCH_PAGE_TOOL: (
        "Вызов запрещён. Ты превысилит лимит вызовов fetch_page в этом ответе — "
        "используй уже загруженное содержимое."
    ),
}


class ToolGuardMiddleware(AgentMiddleware):
    _max_searches_per_turn: int

    def __init__(
        self,
        max_rag_searches_per_turn: int,
        max_web_search_per_turn: int,
        max_page_fetch_per_turn: int,
    ) -> None:
        super().__init__()

        self._limits_per_turn: dict[str, int] = {
            _RAG_TOOL: max_rag_searches_per_turn,
            _WEB_SEARCH_TOOL: max_web_search_per_turn,
            _FETCH_PAGE_TOOL: max_page_fetch_per_turn,
        }

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        name = request.tool_call.get("name", "")
        args = request.tool_call.get("args") or {}
        tool_call_id = request.tool_call.get("id", "")

        if name == _MEMORY_TOOL:
            blocked = self._guard_memory_call(args, request)
            if blocked is not None:
                logger.info(
                    "Блокирую %s (guard): %s | args=%s", _MEMORY_TOOL, blocked, args
                )
                return ToolMessage(
                    content=blocked,
                    name=_MEMORY_TOOL,
                    tool_call_id=tool_call_id,
                )

        limit = self._limits_per_turn.get(name)
        if limit is not None:
            used = self._count_calls_in_turn(request, name)
            if used >= limit:
                logger.info(
                    "Блокирую %s (guard): лимит %s | ход исчерпан | args=%s",
                    name,
                    limit,
                    args,
                )
                return ToolMessage(
                    content=_LIMIT_MESSAGES[name],
                    name=name,
                    tool_call_id=tool_call_id,
                )

        return await handler(request)

    @staticmethod
    def _guard_memory_call(
        args: dict[str, Any], request: ToolCallRequest
    ) -> str | None:
        region = (args.get("region") or "").strip()
        memory = (args.get("memory") or "").strip()

        if not region and not memory:
            return (
                "error: пустой вызов. Сохранять нечего. "
                "Больше не вызывай save_user_facts в этом ответе — "
                "сразу отвечай пользователю."
            )

        profile = request.state.get("user_profile") or {}
        current_region = (profile.get("region_current") or "").strip()
        current_memory = (profile.get("persistent_memory") or "").strip()

        same_region = not region or region == current_region
        same_memory = not memory or memory == current_memory
        if same_region and same_memory:
            return (
                "error: эти данные уже есть в профиле. "
                "Не вызывай save_user_facts — сразу отвечай пользователю."
            )

        return None

    @staticmethod
    def _count_calls_in_turn(request: ToolCallRequest, tool: str) -> int:
        messages = request.state.get("messages") or []
        count = 0
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                break
            if isinstance(msg, ToolMessage) and msg.name == tool:
                count += 1
        return count
