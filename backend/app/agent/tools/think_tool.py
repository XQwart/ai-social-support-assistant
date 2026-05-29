import logging

from langchain.tools import tool, BaseTool

logger = logging.getLogger(__name__)


def make_think_tool() -> BaseTool:
    _called = {"value": False}

    @tool
    def think(thought: str) -> str:
        """Структурированное размышление перед действием.

        Вызывай ПЕРВЫМ и ОДИН РАЗ до любых других инструментов.
        После think — действуй согласно плану, think больше не вызывай.

        Args:
            thought: Анализ и план действий.
        """
        if _called["value"]:
            logger.warning("think вызван повторно — игнорируем")
            return (
                "think уже был вызван. "
                "Немедленно выполни план из предыдущего think и дай финальный ответ. "
                "Больше не вызывай никаких инструментов если это не требуется по плану."
            )

        _called["value"] = True
        logger.debug("Агент думает: %s", thought)
        return thought

    return think
