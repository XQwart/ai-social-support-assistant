from __future__ import annotations
from typing import TYPE_CHECKING, Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest
from langchain_core.messages import AIMessage

if TYPE_CHECKING:
    from langchain.agents.middleware import ModelResponse


class ToolBudgetMiddleware(AgentMiddleware):
    def __init__(self, max_tool_calls: int) -> None:
        self._max_tool_calls = max_tool_calls

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        if self._tool_call_count(request) >= self._max_tool_calls:
            request = request.override(tools=[])
        return await handler(request)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        if self._tool_call_count(request) >= self._max_tool_calls:
            request = request.override(tools=[])
        return handler(request)

    @staticmethod
    def _tool_call_count(request: ModelRequest) -> int:
        messages = request.state.get("messages", [])
        count = 0
        for m in reversed(messages):
            if m.type == "human":
                break
            if isinstance(m, AIMessage):
                count += len(m.tool_calls or [])
        return count
