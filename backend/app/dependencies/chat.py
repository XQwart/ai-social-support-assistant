from typing import Annotated

from fastapi import Depends, Path

from app.exceptions.base_exceptions import NotFoundError, ForbiddenError
from app.dependencies.repositories import ChatRepoDep
from app.dependencies.auth import AuthDep
from app.models import ChatModel


async def get_user_chat(
    token_data: AuthDep,
    chat_rep: ChatRepoDep,
    chat_id: int = Path(...),
) -> ChatModel:
    chat = await chat_rep.get_by_id(chat_id)

    if chat is None:
        raise NotFoundError("Chat not found")

    if chat.user_id != token_data.user_id:
        raise ForbiddenError("Not your chat")

    return chat


OwnerChatDep = Annotated[ChatModel, Depends(get_user_chat)]
