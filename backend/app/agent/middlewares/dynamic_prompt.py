from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from langchain.agents.middleware import dynamic_prompt, ModelRequest

from app.agent.prompts import build_system_prompt

if TYPE_CHECKING:
    from app.agent.state import UserProfile, UserContext


logger = logging.getLogger(__name__)


@dynamic_prompt
def build_dunamic_prompt(request: ModelRequest) -> str:
    ctx: UserContext = request.runtime.context
    profile: UserProfile = request.state.get("user_profile", {})

    region_current = profile.get("region_current")
    effective_region = region_current or ctx.region_reg

    logger.debug(
        "build_system_prompt: first_name=%s, effective_region=%s, "
        "region_current=%s, is_sber=%s, is_new_dialog=%s, "
        "persistent_memory_len=%s",
        ctx.first_name,
        effective_region,
        region_current,
        ctx.is_sber_employee,
        ctx.is_new_dialog,
        len(profile.get("persistent_memory") or ""),
    )

    return build_system_prompt(
        first_name=ctx.first_name,
        effective_region=effective_region,
        region_current=region_current,
        persistent_memory=profile.get("persistent_memory"),
        is_sber_employee=ctx.is_sber_employee,
        is_new_dialog=ctx.is_new_dialog,
    )
