import re
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CERT_DIR = BASE_DIR / "cert"
SOURCES_JSON = DATA_DIR / "sources.json"
FAQ_JSON = DATA_DIR / "faq.json"
CHUCK_JSON = DATA_DIR / "chuck.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CRAWL_INTERVAL = timedelta(hours=72)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_ABBR_SET: set[str] = {
    "ст",
    "п",
    "пп",
    "руб",
    "коп",
    "млн",
    "млрд",
    "тыс",
    "др",
    "пр",
    "т",
    "г",
    "гг",
    "ул",
    "д",
    "кв",
    "обл",
    "см",
    "рис",
    "табл",
    "проф",
    "доц",
    "канд",
    "акад",
    "напр",
    "н",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_NOISE_TAGS: set[str] = {
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "button",
}

_NOISE_ROLES: set[str] = {
    "banner",
    "navigation",
    "complementary",
    "contentinfo",
    "search",
    "menu",
    "menubar",
    "dialog",
}

_NOISE_CLASS_RE = re.compile(
    r"\b(?:cookie|banner|popup|modal|widget|sidebar|menu|breadcrumb|advert|social|share)\b",
    re.I,
)

_BLOCKED_RESOURCES_RE = re.compile(
    r"\.(png|jpg|jpeg|gif|webp|svg|ico|woff2?|ttf|eot|mp4|mp3|avi|css)(\?.*)?$",
    re.I,
)

_MIN_TEXT_LENGTH = 50
