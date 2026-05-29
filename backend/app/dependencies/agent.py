from typing import Annotated

from fastapi import Request, Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.services.agent import AgentToolsScopeFactory


def get_checkpointer(request: Request) -> AsyncPostgresSaver:
    return request.app.state.checkpointer


def get_tools_scope_factory(request: Request) -> AgentToolsScopeFactory:
    return request.app.state.agent_tools_scope_factory


CheckpointerDep = Annotated[AsyncPostgresSaver, Depends(get_checkpointer)]
AgentToolsScopeFactoryDep = Annotated[
    AgentToolsScopeFactory, Depends(get_tools_scope_factory)
]
