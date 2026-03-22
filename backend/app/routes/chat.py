from fastapi import APIRouter, Query
from app.schemas.chat import ChatResponse, ChatsPageResponse
from app.schemas.message import MessageCreate
from app.dependencies.chat import OwnerChatDep
from app.dependencies.auth import AuthDep
from app.dependencies.services import ChatServiceDep
from fastapi import HTTPException

router = APIRouter(prefix="/chats")


@router.post("/")
async def create_chat(
    token_data: AuthDep, chat_service: ChatServiceDep, message: MessageCreate
) -> ChatResponse:
    chat = await chat_service.create_chat(token_data.user_id, message=message.content)

    return chat


@router.get("/")
async def get_chats(
    token_data: AuthDep,
    chat_service: ChatServiceDep,
    limit: int = Query(100),
    offset: int = Query(0),
):
    chats, total = await chat_service.get_chats(
        user_id=token_data.user_id,
        limit=limit,
        offset=offset,
    )

    return ChatsPageResponse(
        items=chats,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{chat_id}")
async def get_chat_info(
    chat: OwnerChatDep,
) -> ChatResponse:
    return chat


@router.delete("/{chat_id}")
async def delete_chat(
    chat: OwnerChatDep,
    chat_service: ChatServiceDep,
):
    success = await chat_service.delete_chat(chat_id=chat.id)

    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
