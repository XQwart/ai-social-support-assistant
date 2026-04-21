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
    async def update_memory(
        region: str | None = None, facts: list[str] | None = None
    ) -> str:
        """Обновить сохранённую информацию о пользователе.

        Вызывай когда пользователь ЯВНО сообщил новые факты о себе:
        регион проживания, состав семьи, статус, доход, инвалидность и т.п.
        НЕ вызывай на гипотетические вопросы или вопросы за других людей.

        Args:
            region: Субъект РФ, если пользователь сообщил место проживания.
                Заполняй, если пользователь
                назвал место проживания ('я живу в Казани' → Республика Татарстан)
                подтвердил регион ('да, живу там' → тот регион, о котором шла речь)
                Если город — определи субъект РФ.
                Если регион не упоминался — пиши None
            facts: Список фактов о пользователе. Включи ВСЕ известные
                   факты (и старые, и новые).
        """

        updates: dict[str, str] = {}
        if region:
            updates["region_current"] = region
        if facts:
            updates["persistent_memory"] = "\n".join(f"- {f}" for f in facts)

        if not updates:
            return "Нечего обновлять"

        try:
            await user_service.update_user_memory(user, **updates)
        except Exception:
            logger.warning("Failed to update user memory", exc_info=True)

        return "Данные обновлены"

    return update_memory
