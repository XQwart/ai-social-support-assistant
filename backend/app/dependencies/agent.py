from typing import Annotated

from fastapi import Request, Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings.embeddings import Embeddings


def get_checkpointer(request: Request) -> AsyncPostgresSaver:
    return request.app.state.checkpointer


CheckpointerDep = Annotated[AsyncPostgresSaver, Depends(get_checkpointer)]
