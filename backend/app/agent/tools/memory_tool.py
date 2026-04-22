from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from langchain.tools import BaseTool, tool

if TYPE_CHECKING:
    from app.models import UserModel
    from app.services import UserService


logger = logging.getLogger(__name__)


def make_memory_tool(user: UserModel, user_service: UserService) -> BaseTool:

    @tool
    async def save_user_facts(
        region: str | None = None, memory: str | None = None
    ) -> str:
        """Сохранить факты о пользователе. Вызывай ОДИН РАЗ за ответ.

        Сохраняй ТОЛЬКО реальные факты о жизни человека.
        НЕЛЬЗЯ сохранять: темы вопросов, описание диалога, свои предположения.

        Args:
            region: Субъект РФ если пользователь назвал где живёт.
                    Город → субъект: "Казань" → "Республика Татарстан".
                    None если регион не упоминался.
            memory: Все известные факты о пользователе одной строкой
                    (старые из профиля + новые).
                    Пример: "трое детей 3, 7, 12 лет, не работает, снимает жильё"
                    None если новых фактов нет.
        """

        if not region and not memory:
            return (
                "Ошибка: необходимо передать хотя бы region или facts. "
                "Вызывай инструмент только когда пользователь сообщил факты о себе."
            )

        updates: dict[str, str] = {}
        if region:
            updates["region_current"] = region
        if memory:
            updates["persistent_memory"] = memory

        if not updates:
            return (
                "Вызов не требовался — пользователь не сообщил новых фактов."
                "Не вызывай этот инструмент повторно, просто ответь пользователю."
            )

        try:
            await user_service.update_user_memory(user, **updates)
        except Exception:
            logger.warning("Failed to update user memory", exc_info=True)

        return (
            "Данные сохранены. Теперь используй полученную информацию "
            "и ответь пользователю на его вопрос."
        )

    return save_user_facts
