from __future__ import annotations
from typing import TYPE_CHECKING

from langchain.tools import BaseTool, tool

if TYPE_CHECKING:
    from app.models import UserModel
    from app.services import RegionService, RAGService
    from app.schemas.rag_schemas import RetrievedChunk


def make_retrive_tool(
    user: UserModel, rag_service: RAGService, region_service: RegionService
) -> BaseTool:

    @tool
    async def search_knowledge_base(query: str, region_name: str | None = None) -> str:
        """Поиск в базе знаний по мерам социальной поддержки граждан РФ.

        ОБЯЗАТЕЛЬНО вызывай при любом вопросе о льготах, пособиях, субсидиях,
        выплатах, компенсациях, документах и условиях их получения.
        Без вызова этого инструмента называть суммы и условия НЕЛЬЗЯ.

        Вызывай НЕСКОЛЬКО РАЗ с разными формулировками одной темы —
        это повышает шанс найти нужный документ.

        Как формулировать query (КРИТИЧЕСКИ ВАЖНО):
        Запрос — это НЕ пересказ вопроса пользователя, а короткая фраза
        из официального документа или нормативного акта.

        Стратегия multi-query: для одной темы сделай 2-3 вызова:
        1. Официальное название меры поддержки
            ("единовременное пособие при рождении ребёнка")
        2. Ключевые слова + условия
            ("выплата при рождении первого ребёнка размер условия")
        3. Региональный аспект, если известен
            ("пособие рождение ребёнка Свердловская область")

        Примеры перевода вопросов пользователя в query:
        "сколько платят за рождение ребёнка"
            → "единовременное пособие при рождении ребёнка размер"
            → "выплата при рождении ребёнка условия назначения"
        "льготы многодетным в Екатеринбурге"
            → "меры социальной поддержки многодетных семей Свердловская область"
            → "льготы многодетным региональные выплаты Свердловская область"
        "что положено пенсионеру"
            → "ежемесячная денежная выплата пенсионерам условия"
            → "меры поддержки пенсионеров федеральные льготы"
        "льготы работникам сбербанка при рождении ребёнка"
            → "корпоративные выплаты сотрудникам рождение ребёнка"
            → "льготы сотрудникам банка пособие новорождённый"

        Args:
            query: Короткая фраза в стиле официального документа (не вопрос).
            region_name: Субъект РФ, если известен. Примеры: "Свердловская область",
                        "Москва", "Республика Татарстан". None если неизвестен.
        """

        region_code = await region_service.get_code_by_name(region_name=region_name)

        response = await rag_service.retrieve(
            query, region=region_code, place_of_work=user.place_of_work
        )

        public_chunks = [c for c in response if not c.is_internal]
        internal_chunks = (
            [c for c in response if c.is_internal] if user.is_sber_employee else []
        )

        return (
            _format_chunks(public_chunks, internal_chunks)
            if public_chunks or internal_chunks
            else "В базе знаний не найдено релевантных документов по этому запросу."
        )

    return search_knowledge_base


def _format_chunks(
    public: list[RetrievedChunk],
    internal: list[RetrievedChunk],
) -> str:
    parts = []
    if public:
        entries = [
            f"Источник: {c.source_name}\nURL: {c.source_url}\nТекст:\n{c.text}"
            for c in public
        ]
        parts.append("ПУБЛИЧНЫЕ ИСТОЧНИКИ:\n\n" + "\n\n---\n\n".join(entries))
    if internal:
        entries = [f"Текст:\n{c.text}" for c in internal]
        parts.append(
            "ВНУТРЕННИЕ ИСТОЧНИКИ ПАО СБЕРБАНК "
            "(не раскрывай URL и реквизиты):\n\n" + "\n\n---\n\n".join(entries)
        )
    return "\n\n===\n\n".join(parts)
