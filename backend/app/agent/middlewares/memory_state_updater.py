from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from app.agent.tools.memory_tool import merge_persistent_memory


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
        current_profile = dict(request.state.get("user_profile", {}))

        changed = False
        if region := args.get("region"):
            current_profile["region_current"] = region
            changed = True
        if memory := args.get("memory"):
            current_profile["persistent_memory"] = merge_persistent_memory(
                current_profile.get("persistent_memory"), memory
            )
            changed = True

        if not changed:
            return result

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
