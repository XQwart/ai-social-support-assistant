from dataclasses import dataclass
from typing import TypedDict

from langchain.agents import AgentState


class UserProfile(TypedDict, total=False):
    region_current: str | None
    persistent_memory: str | None


class SOCAgentState(AgentState):
    user_profile: UserProfile


@dataclass
class UserContext:
    first_name: str
    region_reg: str | None
    is_sber_employee: bool
    is_new_dialog: bool
