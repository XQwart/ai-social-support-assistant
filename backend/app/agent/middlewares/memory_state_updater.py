from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command


class MemoryToolStateMiddleware(AgentMiddleware):
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        result = await handler(request)

        if request.tool_call["name"] != "save_user_facts":
            return result

        args = request.tool_call.get("args", {})
        state_update: dict[str, Any] = {}
        if region := args.get("region"):
            state_update["region_current"] = region
        if memory := args.get("memory"):
            state_update["persistent_memory"] = memory

        if not state_update:
            return result

        current_profile = dict(request.state.get("user_profile", {}))
        current_profile.update(state_update)

        if isinstance(result, Command):
            merged = {**(result.update or {}), "user_profile": current_profile}
            return Command(
                update=merged,
                graph=result.graph,
                resume=result.resume,
                goto=result.goto,
            )

        return Command(
            update={
                "messages": [result],
                "user_profile": current_profile,
            }
        )
