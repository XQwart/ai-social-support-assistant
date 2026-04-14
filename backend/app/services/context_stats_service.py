from __future__ import annotations
from typing import TYPE_CHECKING

from app.schemas.chat_schemas import ChatContextStats

if TYPE_CHECKING:
    from app.repositories import ContextStatsRepository, ChatRepository
    from app.models import ChatModel


class ContextStatsService:
    _ctx_stats_rep: ContextStatsRepository
    _chat_rep: ChatRepository

    def __init__(
        self, ctx_stats_rep: ContextStatsRepository, chat_rep: ChatRepository
    ) -> None:
        self._ctx_stats_rep = ctx_stats_rep
        self._chat_rep = chat_rep

    async def get_chat_stats(self, chat: ChatModel) -> ChatContextStats:
        deltas = await self._ctx_stats_rep.get_recent_deltas(chat_id=chat.id)

        return ChatContextStats(
            last_total_tokens=chat.last_total_tokens,
            reserve_input_tokens=chat.reserve_input_tokens,
            recent_input_deltas=deltas,
        )

    async def update_chat_stats(self, chat: ChatModel, **fields) -> None:
        if "recent_input_deltas" in fields:
            await self._ctx_stats_rep.set_recent_deltas(
                chat.id, deltas=fields["recent_input_deltas"]
            )

        await self._chat_rep.update(
            chat,
            **{k: v for k, v in fields.items() if k != "recent_input_deltas"},
        )
