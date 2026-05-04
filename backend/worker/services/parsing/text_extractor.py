import trafilatura


class HtmlTextExtractor:
    def extract_text(self, html: str, url: str) -> str | None:
        text = trafilatura.extract(
            html,
            url=url,
            include_tables=True,
            include_comments=False,
            include_links=False,
            favor_recall=True,
            deduplicate=True,
        )

        if not text:
            return None

        return text
