from pydantic import BaseModel


class WebSearchPage(BaseModel):
    url: str
    title: str = ""
    content: str = ""


class WebSearchResult(BaseModel):
    results: list[WebSearchPage] = []