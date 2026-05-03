from __future__ import annotations
from typing import TYPE_CHECKING
import re

from langchain_core.tools import tool, BaseTool

from app.schemas.page_fetch_schemas import FetchErrorKind
from app.utils import text_utils

if TYPE_CHECKING:
    from app.core.config import Config
    from app.services.page_fetch_service import PageFetchService
    from app.schemas.page_fetch_schemas import FetchResult


_ERROR_ANSWERS = {
    FetchErrorKind.BLOCKED: "URL заблокирован: ведет во внутреннюю сеть или использует неподдерживаемый протокол",
    FetchErrorKind.HTTP_STATUS: "Сайт ответил ошибкой: {detail}",
    FetchErrorKind.UNSUPPORTED_TYPE: "Неподдерживаемый тип содержимого по этой ссылке. Поддерживаются только HTML и PDF",
    FetchErrorKind.EMPTY_CONTENT: "Страница пуста, или не удалось извлечь текст. Возможно, контент рендерится JavaScript'ом",
    FetchErrorKind.NETWORK: "Неудалось подключиться к сайту. Возможно, сайт недоступен или есть временные сетевые проблемы.",
    FetchErrorKind.UNEXPECTED: "Произошла внутренняя ошибка при обработке документа.",
    FetchErrorKind.TOO_LARGE: "Размер файла слишком большой для обработки.",
}


def make_page_fetch_tool(
    page_fetch_service: PageFetchService, config: Config
) -> BaseTool:
    content_limit = config.fetch_max_output

    @tool
    async def fetch_page(urls: list[str]) -> str:
        """Инструмент для парсинга веб-страницы"""  # TODO: Добавить нормальный докстринг

        max_urls = config.agent_page_fetch_max_urls_tool
        if len(urls) >= max_urls:
            return f"Нельзя передавать больше {max_urls} ссылок за один вызов."

        results = await page_fetch_service.fetch_many(urls)

        return _format_results(results)

    def _format_results(results: list[FetchResult]) -> str:
        parts: list[str] = ["## Результаты чтения веб-страниц"]

        for i, result in enumerate(results):
            if not result.has_error:
                title = result.title if result.title else f"Без названия {i}"
                header = f"### [{title}]({result.url})"

                content = _demote_headings(result.content)
                if len(content) > content_limit:
                    content = text_utils.shorten_block(content, content_limit)
                    header += " (обрезано)"

                parts.append(f"{header}\n\n{content}")
            else:
                template = _ERROR_ANSWERS[result.error_kind]

                header = f"### [Ошибка при парсинге]({result.url})"
                content = (
                    template.format(detail=result.error_detail)
                    if "{detail}" in template
                    else template
                )

            parts.append(f"{header}\n\n{content}")

        return "\n\n---\n\n".join(parts)

    def _demote_headings(text: str, levels: int = 3) -> str:
        def shift(match: re.Match[str]) -> str:
            hashes = match.group(1)
            new_level = min(len(hashes) + levels, 6)
            return "#" * new_level + match.group(2)

        return re.sub(r"^(#{1,6})(\s+)", shift, text, flags=re.MULTILINE)

    return fetch_page
