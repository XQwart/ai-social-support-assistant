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
        """Обновить сохранённую информацию о пользователе.

        Вызывай ОДНОКРАТНО когда пользователь явно сообщил новые факты о себе.
        Никогда не вызывай этот инструмент больше одного раза за один ответ.

        memory — это ПОЛНЫЙ актуальный портрет пользователя: включи всё что
        уже было известно (из профиля выше) ПЛЮС новые факты из текущего сообщения.
        Пиши связным текстом, кратко, только реальные факты о человеке.

        СОХРАНЯТЬ (пользователь прямо сказал о себе):
        + "живу в Казани, трое детей 3, 7 и 12 лет, не работаю"
        + "инвалидность 2 группа, муж работает, снимаем жильё"

        НЕ СОХРАНЯТЬ:
        - темы вопросов ("спросил про выплаты", "интересовался маткапиталом")
        - поведение в диалоге ("задавал вопросы", "хочет узнать больше")
        - твои предположения ("возможно нужна помощь", "заинтересован в...")

        Простой тест: пользователь произнёс вслух факт о своей жизни?
        Если нет — НЕ вызывай.

        Args:
            region: Субъект РФ если пользователь назвал место проживания.
                    Определи субъект по городу: "Казань" → "Республика Татарстан".
                    None если регион не упоминался.
            memory: Полный текстовый портрет пользователя — старые факты
                    из профиля плюс новые. Например:
                    "Трое детей (3, 7 и 12 лет). Не работает. Снимает жильё.
                    Планирует оформить субсидию на ЖКХ."
                    None если нечего сохранять.
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

        return "Данные обновлены"

    return save_user_facts
