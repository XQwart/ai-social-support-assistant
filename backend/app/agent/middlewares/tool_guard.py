from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command


logger = logging.getLogger(__name__)


SEARCH_TOOL = "search_knowledge_base"
MEMORY_TOOL = "save_user_facts"


class ToolGuardMiddleware(AgentMiddleware):
    _max_searches_per_turn: int

    def __init__(self, max_searches_per_turn: int) -> None:
        super().__init__()

        self._max_searches_per_turn = max_searches_per_turn

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        name = request.tool_call.get("name", "")
        args = request.tool_call.get("args") or {}
        tool_call_id = request.tool_call.get("id", "")

        if name == MEMORY_TOOL:
            blocked = self._guard_memory_call(args, request)
            if blocked is not None:
                logger.info(
                    "Блокирую %s (guard): %s | args=%s", MEMORY_TOOL, blocked, args
                )
                return ToolMessage(
                    content=blocked,
                    name=MEMORY_TOOL,
                    tool_call_id=tool_call_id,
                )

        if name == SEARCH_TOOL:
            search_count = self._count_searches_in_turn(request)
            if search_count > self._max_searches_per_turn:
                logger.info("Блокирую %s (guard) | args=%s", SEARCH_TOOL, args)
                return ToolMessage(
                    content=(
                        "Вызов запрещён. Ты уже получил результат "
                        "search_knowledge_base в этом ответе — используй его. "
                        "Отвечай пользователю на основе уже найденных данных; "
                        "если их недостаточно, задай один уточняющий вопрос."
                    ),
                    name=SEARCH_TOOL,
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
    def _count_searches_in_turn(request: ToolCallRequest) -> int:
        messages = request.state.get("messages") or []
        count = 0
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                break
            if isinstance(msg, ToolMessage) and msg.name == SEARCH_TOOL:
                count += 1
        return count
