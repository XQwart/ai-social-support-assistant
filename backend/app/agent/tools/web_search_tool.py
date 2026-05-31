from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from urllib.parse import unquote

from langchain_core.tools import tool, BaseTool

from app.exceptions.base_exceptions import ExternalServiceError
from app.utils import text_utils

if TYPE_CHECKING:
    from app.core.config import Config
    from app.services import WebSearchService
    from app.schemas.web_search_schemas import WebSearchPage


logger = logging.getLogger(__name__)

_LOG_PREFIX = "search_web:"


def make_search_web_tool(
    web_search_service: WebSearchService, config: Config
) -> BaseTool:
    citation_limit = config.web_search_citation_char_limit

    @tool
    async def search_web(query: str) -> str:
        """Поиск актуальной информации в интернете по сайтам о соцподдержке РФ.

        Когда вызывать:
        - search_knowledge_base уже был вызван и вернул "Релевантных
        документов в базе не найдено", а вопрос пользователя по своей
        природе фактологический (пособие, льгота, выплата, субсидия,
        порядок оформления, контакты ведомства).
        - Вопрос про актуальные значения, которые меняются во времени:
        размер выплаты в текущем году, индексация, новые региональные
        программы, изменения сроков подачи. База знаний может содержать
        устаревшие данные — веб даст свежие.
        - Пользователь явно просит проверить «как сейчас», «в 2026 году»,
        «после такой-то даты», «свежая информация».

        Когда НЕ вызывать:
        - Приветствия, благодарности, прощания, общая болтовня.
        - Вопрос, на который уже дан осмысленный ответ из
        search_knowledge_base — не дублируй веб-поиском.
        - Вопросы, не относящиеся к соцподдержке (программирование,
        развлечения, советы по жизни и т.п.). Веб-поиск только по теме.

        ЛИМИТ: РОВНО 1 вызов на одно сообщение пользователя.
        После получения результата повторный вызов ЗАПРЕЩЁН, даже если ты:
        - изменил query (порядок слов, падеж, синонимы);
        - решил уточнить формулировку или сузить регион;
        - получил мало результатов и хочешь "ещё разок".
        Изменение параметров НЕ делает вызов новым. Middleware перехватит
        и вернёт ошибку — не трать ход.

        Если результат пустой или не покрывает вопрос — НЕ ищи повторно.
        Честно скажи пользователю, что точной информации найти не удалось

        ФОРМАТ ВХОДНОГО ЗАПРОСА:
        Поисковый запрос как фрагмент документа, не как вопрос. Включай
        регион, если он известен из профиля или сообщения пользователя.
            Плохо: "что мне положено за ребёнка в Свердловской области"
            Хорошо: "единовременное пособие при рождении ребёнка
                    Свердловская область размер 2026"

        Args:
            query: Поисковый запрос для веб-поиска. Формулируй как
                фрагмент документа с ключевыми словами (пособие,
                выплата, регион, год, категория получателя), а не
                как разговорный вопрос.
        """

        try:
            response = await web_search_service.search(query)
        except ExternalServiceError:
            logger.exception(
                "%s веб-поиск завершился ошибкой query='%s'",
                _LOG_PREFIX,
                query,
                exc_info=True,
            )
            return (
                "Онлайн-поиск сейчас недоступен. Скажи пользователю, что "
                "не удалось проверить актуальную информацию в интернете, "
                "и ответь по базе знаний или предложи попробовать позже."
            )

        logger.exception(
            "%s количество найденых источников: %d; query='%s'",
            _LOG_PREFIX,
            len(response.results),
            query,
            exc_info=True,
        )

        if not response.results:
            return "Веб-поиск ничего не нашёл по этому запросу."

        return _formate_results(response.results)

    def _formate_results(pages: list[WebSearchPage]) -> str:
        parts = ["## Результаты поиска в интернете"]
        parts.extend(
            [_render_page(page, i) for i, page in enumerate(pages) if page.url]
        )

        return "\n\n".join(parts)

    def _render_page(page: WebSearchPage, idx: int) -> str:
        title = (page.title or f"Источник {idx}").strip()
        url = unquote(page.url)

        header = f"### [{title}]({url}) - Веб"
        citation = text_utils.shorten_inline(page.content, citation_limit)
        return f"{header}\n>: {citation}"

    return search_web
