"""Middleware that enforces tool-use contracts the LLM often breaks.

It short-circuits calls BEFORE they reach the real tool, so bad patterns
never cost an extra round-trip to the knowledge base / database:

- empty ``save_user_facts()`` — the model calls the tool with no args
  hoping something will be saved. We reject with a recovery instruction.
- duplicate ``search_knowledge_base`` within the same user turn —
  paraphrased queries, padezh changes, or toggling ``region_name`` do
  not count as new searches. We return the previous tool output so the
  model can simply answer from it.
- ``save_user_facts`` that only repeats data already in the profile —
  no point writing the same string back to the DB.

This middleware does NOT replace ``ToolBudgetMiddleware``; it complements
it by stopping specific misuse patterns that the simple counter misses.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command


logger = logging.getLogger(__name__)


SEARCH_TOOL = "search_knowledge_base"
MEMORY_TOOL = "save_user_facts"


class ToolGuardMiddleware(AgentMiddleware):
    """Reject malformed / redundant tool calls before they execute."""

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
            prior = self._previous_search_in_turn(request)
            if prior is not None:
                logger.info(
                    "Блокирую повторный %s (guard) | args=%s", SEARCH_TOOL, args
                )
                return ToolMessage(
                    content=(
                        "Повторный вызов запрещён. Ты уже получил результат "
                        "search_knowledge_base в этом ответе — используй его. "
                        "Отвечай пользователю на основе уже найденных данных; "
                        "если их недостаточно, задай один уточняющий вопрос."
                    ),
                    name=SEARCH_TOOL,
                    tool_call_id=tool_call_id,
                )

        return await handler(request)

    # ------------------------------------------------------------------
    # save_user_facts guards
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # search_knowledge_base duplicate detection
    # ------------------------------------------------------------------
    @staticmethod
    def _previous_search_in_turn(request: ToolCallRequest) -> ToolMessage | None:
        """Return the previous successful search ToolMessage in this turn.

        A "turn" is everything after the last HumanMessage. If we find a
        ``search_knowledge_base`` ToolMessage there, a new search is a
        duplicate regardless of parameter tweaks.
        """
        messages = request.state.get("messages") or []
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return None
            if isinstance(msg, ToolMessage) and msg.name == SEARCH_TOOL:
                return msg
            # AIMessages with tool_calls are fine; we look for ToolMessage
            # responses as the signal of a completed search.
            if isinstance(msg, AIMessage):
                continue
        return None
