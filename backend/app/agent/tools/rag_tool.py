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

        Вызывай когда пользователь спрашивает о конкретных льготах, пособиях,
        субсидиях, выплатах, услугах соцзащиты. НЕ вызывай на приветствия,
        благодарности и офф-топик.

        Если нужно найти информацию по нескольким разным темам — вызови
        эту функцию несколько раз с разными query.

        Args:
            query: Поисковый запрос, переформулированный для семантического
                   поиска. Например, если пользователь спросил "что мне
                   положено", а из контекста понятно что речь о пособиях
                   для многодетных — пиши "пособия для многодетных семей".
            region_name: Название субъекта РФ, если известно из контекста
                    диалога. Например: "Краснодарский край",
                    "Республика Татарстан", "Москва".
                    Передавай None если регион неизвестен.
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
