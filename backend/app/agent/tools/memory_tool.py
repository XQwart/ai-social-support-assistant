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
        """Сохранить НОВЫЙ факт о пользователе.

        ЗАПРЕЩЕНО вызывать этот инструмент без параметров или со всеми
        параметрами равными None/пустой строке. Если сохранять нечего —
        НЕ вызывай инструмент вообще, сразу переходи к ответу пользователю.

        Когда вызывать: пользователь в последнем сообщении сообщил реальный
        факт о своей жизни, которого ещё НЕТ в профиле и в блоке
        «Известные факты».

        Когда НЕ вызывать:
        - факт уже есть в профиле (имя, регион, флаг сотрудника);
        - факт уже перечислен в блоке «Известные факты»;
        - пользователь задал вопрос, но нового факта о себе не сообщил;
        - ты хочешь сохранить тему диалога, вопрос или своё предположение;
        - у тебя нет данных для хотя бы одного параметра — НЕ вызывай.

        Максимум 1 вызов на одно сообщение пользователя. Повторный вызов
        после получения ответа от инструмента — запрещён.

        Args:
            region: Субъект РФ, если пользователь ВПЕРВЫЕ назвал место жительства.
                    Город → субъект: "Казань" → "Республика Татарстан".
                    None, если регион не упоминался или уже известен из профиля.
            memory: Все факты о пользователе одной строкой (старые + новый).
                    Пример: "трое детей 3, 7, 12 лет, не работает, снимает жильё".
                    None, если новых фактов нет.
        """

        updates: dict[str, str] = {}
        if region:
            updates["region_current"] = region
        if memory:
            updates["persistent_memory"] = memory

        if not updates:
            return (
                "error: пустой вызов. "
                "Больше не вызывай save_user_facts в этом ответе — "
                "сохранять нечего. Сразу отвечай пользователю."
            )

        try:
            await user_service.update_user_memory(user, **updates)
        except Exception:
            logger.warning("Failed to update user memory", exc_info=True)
            return "error: сохранение не выполнено"

        return "saved"

    return save_user_facts
