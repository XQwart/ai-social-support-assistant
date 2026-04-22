from __future__ import annotations
from typing import TYPE_CHECKING

from langchain.agents.middleware import dynamic_prompt, ModelRequest

from app.agent.prompts import build_system_prompt

if TYPE_CHECKING:
    from app.agent.state import UserProfile, UserContext


@dynamic_prompt
def build_dunamic_prompt(request: ModelRequest) -> str:
    ctx: UserContext = request.runtime.context
    profile: UserProfile = request.state.get("user_profile", {})

    region_current = profile.get("region_current")

    return build_system_prompt(
        first_name=ctx.first_name,
        effective_region=region_current or profile.get("region_reg"),
        region_current=region_current,
        persistent_memory=profile.get("persistent_memory"),
        is_sber_employee=ctx.is_sber_employee,
        is_new_dialog=ctx.is_new_dialog,
    )
