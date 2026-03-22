from typing import Annotated

from fastapi import Depends, HTTPException, Path

from app.models.chat import Chat
from app.dependencies.repositories import ChatRepoDep
from app.dependencies.auth import AuthDep


async def get_user_chat(
    token_data: AuthDep,
    chat_rep: ChatRepoDep,
    chat_id: int = Path(...),
) -> Chat:
    chat = await chat_rep.get_by_id(chat_id)

    if chat is None:
        raise HTTPException(404, "Chat not found")

    if chat.user_id != token_data.user_id:
        raise HTTPException(403, "Not your chat")

    return chat


OwnerChatDep = Annotated[Chat, Depends(get_user_chat)]
