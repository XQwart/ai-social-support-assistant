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
        region: str | None = None, facts: list[str] | None = None
    ) -> str:
        """Обновить сохранённую информацию о пользователе.

        Вызывай ТОЛЬКО когда пользователь ЯВНО сообщил НОВЫЕ конкретные факты о себе:
        регион проживания, состав семьи, статус, доход, инвалидность и т.п.

        НЕ вызывай в следующих случаях:
        - Приветствия, прощания, благодарности, small talk
        - Гипотетические вопросы или вопросы за других людей
        - Если нет НОВЫХ фактов для сохранения
        - Если пользователь просто задаёт вопрос, ничего не сообщая о себе

        Если вызывать не нужно — просто отвечай пользователю напрямую,
        БЕЗ вызова этого инструмента.

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

        if not region and not facts:
            return (
                "Ошибка: необходимо передать хотя бы region или facts. "
                "Если пользователь не сообщил новых фактов — не вызывай этот инструмент."
            )

        updates: dict[str, str] = {}
        if region:
            updates["region_current"] = region
        if facts:
            updates["persistent_memory"] = "\n".join(f"- {f}" for f in facts)

        if not updates:
            return (
                "Вызов не требовался — пользователь не сообщил новых фактов."
                "Не вызывай этот инструмент повторно, просто ответь пользователю."
            )

        try:
            await user_service.update_user_memory(user, **updates)
        except Exception:
            logger.warning("Failed to update user memory", exc_info=True)

        return "Данные обновлены"

    return save_user_facts
