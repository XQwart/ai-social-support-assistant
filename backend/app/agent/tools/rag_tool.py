from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from langchain.tools import BaseTool, tool

if TYPE_CHECKING:
    from app.models import UserModel
    from app.services import RegionService, RAGService
    from app.schemas.rag_schemas import RetrievedChunk


logger = logging.getLogger(__name__)


# Soft limit on the citation length we pre-format for the model.
# A full chunk text can be thousands of chars; the model only needs a
# short quote to cite, not the whole paragraph.
_CITATION_CHAR_LIMIT = 220

# Upper bound on the full chunk text we include for context.
_CHUNK_TEXT_CHAR_LIMIT = 1400


def make_retrive_tool(
    user: UserModel, rag_service: RAGService, region_service: RegionService
) -> BaseTool:

    @tool
    async def search_knowledge_base(query: str, region_name: str | None) -> str:
        """Поиск по базе знаний о мерах социальной поддержки в РФ.

        Когда вызывать: пользователь задал фактологический вопрос о льготе,
        пособии, выплате, субсидии, сроках, размерах, условиях; либо
        спрашивает «как оформить/подать/получить», «куда обратиться».
        Когда НЕ вызывать: приветствия, благодарности, прощания,
        общие реплики не о соцподдержке.

        ЛИМИТ: РОВНО 1 вызов на одно сообщение пользователя.
        После получения результата повторный вызов ЗАПРЕЩЁН,
        даже если ты:
        - изменил query (порядок слов, падеж, синонимы);
        - добавил или убрал region_name;
        - решил уточнить формулировку.
        Изменение параметров НЕ делает вызов новым. Middleware
        перехватит и вернёт ошибку — не трать ход.

        Если результат пустой или неполный — НЕ ищи повторно.
        Задай пользователю один уточняющий вопрос или честно скажи,
        что точной информации в базе нет.

        Передавай ОБА параметра сразу в первом и единственном вызове:
        заполни region_name, если регион известен из профиля или сообщения
        пользователя.

        ФОРМАТ ОТВЕТА (важно!): инструмент возвращает готовые блоки
        Markdown вида:
            ### [Название](URL) — Регион
            > готовая цитата
            Полный текст: ...
        Для ответа пользователю бери заголовок (### ...) и строку с цитатой
        (> ...) КАК ЕСТЬ — не переписывай URL, не выдумывай новые
        реквизиты. Если у блока URL = «—», ссылку НЕ ставь.

        Фильтрация источников по доступу (публичные / внутренние ПАО Сбербанк)
        выполняется на стороне backend по флагу профиля пользователя.
        Модель не может её обойти.

        Args:
            query: Поисковый запрос как фрагмент документа, не как вопрос.
                   Плохо: "что мне положено за ребёнка"
                   Хорошо: "единовременное пособие при рождении ребёнка размер"
            region_name: Субъект РФ из профиля или сообщения пользователя.
                         Например: "Московская область", "Республика Татарстан".
                         None, только если регион реально неизвестен.
        """

        region_code = await region_service.get_code_by_name(region_name=region_name)

        response = await rag_service.retrieve(
            query, region=region_code, place_of_work=user.place_of_work
        )

        public_chunks = [c for c in response if not c.is_internal]
        internal_chunks = (
            [c for c in response if c.is_internal] if user.is_sber_employee else []
        )

        if not public_chunks and not internal_chunks:
            logger.info("RAG: релевантные документы не найдены для query=%r", query)
            return (
                "Релевантных документов в базе не найдено. "
                "Не придумывай факты: скажи пользователю, что точной "
                "информации по запросу в базе нет, и предложи проверить "
                "на gosuslugi.ru или sfr.gov.ru."
            )

        return _format_chunks(public_chunks, internal_chunks, region_name)

    return search_knowledge_base


def _format_chunks(
    public: list[RetrievedChunk],
    internal: list[RetrievedChunk],
    region_name: str | None,
) -> str:
    """Render chunks as ready-to-copy Markdown blocks.

    Each chunk becomes a block of the form::

        ### [Название источника](URL) — Регион
        > короткая цитата
        Полный текст: ...

    The model is instructed (in the tool docstring and system prompt) to
    copy the ``###`` header and the ``>`` quote verbatim into its answer.
    """

    parts: list[str] = []

    if public:
        parts.append("## Публичные источники\n")
        parts.extend(
            _render_chunk(c, region_name, idx)
            for idx, c in enumerate(public, start=1)
        )

    if internal:
        parts.append(
            "\n## Внутренние источники ПАО Сбербанк\n"
            "ВАЖНО: в ответе пользователю НЕ указывай URL, "
            "ссылайся как «согласно внутренним документам ПАО Сбербанк»."
        )
        parts.extend(
            _render_internal_chunk(c, idx)
            for idx, c in enumerate(internal, start=1)
        )

    return "\n\n".join(parts)


def _render_chunk(
    chunk: RetrievedChunk, region_name: str | None, idx: int
) -> str:
    title = (chunk.source_name or f"Источник {idx}").strip()
    url = (chunk.source_url or "").strip()
    region_label = (region_name or "РФ").strip() or "РФ"
    citation = _shorten(chunk.text, _CITATION_CHAR_LIMIT)
    full_text = _shorten(chunk.text, _CHUNK_TEXT_CHAR_LIMIT)

    if url:
        header = f"### [{title}]({url}) — {region_label}"
    else:
        header = f"### {title} — {region_label}\n(URL отсутствует — ссылку НЕ придумывай)"

    return f"{header}\n> {citation}\n\nПолный текст:\n{full_text}"


def _render_internal_chunk(chunk: RetrievedChunk, idx: int) -> str:
    citation = _shorten(chunk.text, _CITATION_CHAR_LIMIT)
    full_text = _shorten(chunk.text, _CHUNK_TEXT_CHAR_LIMIT)
    return (
        f"### Внутренний документ {idx} (URL не публикуется)\n"
        f"> {citation}\n\n"
        f"Полный текст:\n{full_text}"
    )


def _shorten(text: str, limit: int) -> str:
    text = (text or "").strip().replace("\r\n", "\n")
    if len(text) <= limit:
        return text
    # Cut on a word boundary when possible so the quote reads cleanly.
    cut = text.rfind(" ", 0, limit)
    if cut < limit // 2:
        cut = limit
    return text[:cut].rstrip(" ,.;:—-") + "…"
