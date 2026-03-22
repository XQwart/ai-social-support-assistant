import httpx
from bs4 import BeautifulSoup


def parse_site(url: str) -> str:
    with httpx.Client() as client:
        html = client.get(url).text

    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body")

    for tag in body(["script", "style"]):
        tag.decompose()

    return body.get_text(separator=" ", strip=True)
