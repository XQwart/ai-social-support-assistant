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

ABBR_SET: set[str] = {
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

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

NOISE_TAGS: set[str] = {
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

NOISE_ROLES: set[str] = {
    "banner",
    "navigation",
    "complementary",
    "contentinfo",
    "search",
    "menu",
    "menubar",
    "dialog",
}

NOISE_CLASS_RE = re.compile(
    r"\b(?:cookie|banner|popup|modal|widget|sidebar|menu|breadcrumb|advert|social|share"
    r"|header|footer|nav|navigation|search|pagination|pager|toolbar|panel|top-bar"
    r"|feedback|rating|vote|print|back-link|related|recommend|tags|rubric)\b",
    re.I,
)

BLOCKED_RESOURCES_RE = re.compile(
    r"\.(png|jpg|jpeg|gif|webp|svg|ico|woff2?|ttf|eot|mp4|mp3|avi|css)(\?.*)?$",
    re.I,
)

MIN_TEXT_LENGTH = 50


MAIN_CONTENT_SELECTORS = (
    "main",
    "article",
    "[role='main']",
    ".content",
    ".page-content",
    ".entry-content",
    ".article-content",
    ".post-content",
    ".news-detail",
    ".news-item",
    ".text-content",
    ".main-content",
    ".content-wrapper",
    "#content",
    "#main",
    "#primary",
)

DROP_LINE_PATTERNS = (
    re.compile(r"^\s*←?\s*назад\s*$", re.IGNORECASE),
    re.compile(r"^\s*контакты\s*$", re.IGNORECASE),
    re.compile(r"^\s*все новости\s*$", re.IGNORECASE),
    re.compile(r"^\s*все конкурсы\s*$", re.IGNORECASE),
    re.compile(r"^\s*поделиться\s*$", re.IGNORECASE),
    re.compile(r"^\s*печать\s*$", re.IGNORECASE),
    re.compile(r"^\s*версия для слабовидящих\s*$", re.IGNORECASE),
    re.compile(r"^\s*электронная приемная\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d{1,2}:\d{2}\s*$"),
    re.compile(r"^\s*главная\s*$", re.IGNORECASE),
    re.compile(r"^\s*на главную\s*$", re.IGNORECASE),
    re.compile(r"^\s*подробнее\s*$", re.IGNORECASE),
    re.compile(r"^\s*читать далее\s*$", re.IGNORECASE),
    re.compile(r"^\s*скачать\s*$", re.IGNORECASE),
    re.compile(r"^\s*скачать файл\s*$", re.IGNORECASE),
    re.compile(r"^\s*перейти\s*$", re.IGNORECASE),
    re.compile(r"^\s*подписаться\s*$", re.IGNORECASE),
    re.compile(r"^\s*отправить\s*$", re.IGNORECASE),
    re.compile(r"^\s*официальный сайт.*$", re.IGNORECASE),
    re.compile(r"^\s*©.*$", re.IGNORECASE),
    re.compile(r"^\s*все права защищены.*$", re.IGNORECASE),
    re.compile(r"^\s*\d{4}\s*год[а-я]*\s*$", re.IGNORECASE),
)

STOP_SECTION_PATTERNS = (
    re.compile(r"^\s*часто задаваемые вопросы\s*$", re.IGNORECASE),
    re.compile(r"^\s*куда обращаться\s*$", re.IGNORECASE),
    re.compile(
        r"^\s*список отделов социальной защиты населения.*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*список отделений социального фонда.*$",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*показать все\s*\(\d+\)\s*$", re.IGNORECASE),
)

IRRELEVANT_PARENT_MARKERS = (
    "menu",
    "nav",
    "breadcrumb",
    "footer",
    "header",
    "sidebar",
    "pager",
    "share",
    "social",
    "related",
    "recommend",
    "contact",
)


SKIP_SCHEMES = {"mailto", "tel", "javascript", "data"}

SKIP_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".css",
    ".js",
    ".xml",
)

DOCUMENT_EXTENSIONS = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".odt",
    ".ods",
    ".rtf",
)

SKIP_PATH_PATTERNS = (
    re.compile(r"/search", re.IGNORECASE),
    re.compile(r"/login", re.IGNORECASE),
    re.compile(r"/auth", re.IGNORECASE),
    re.compile(r"/signin", re.IGNORECASE),
    re.compile(r"/logout", re.IGNORECASE),
    re.compile(r"/register", re.IGNORECASE),
    re.compile(r"/cart", re.IGNORECASE),
    re.compile(r"/basket", re.IGNORECASE),
    re.compile(r"/compare", re.IGNORECASE),
    re.compile(r"/print", re.IGNORECASE),
    re.compile(r"/feed", re.IGNORECASE),
    re.compile(r"/tag/", re.IGNORECASE),
    re.compile(r"/photo", re.IGNORECASE),
    re.compile(r"/gallery", re.IGNORECASE),
    re.compile(r"/image", re.IGNORECASE),
    re.compile(r"/video", re.IGNORECASE),
    re.compile(r"/media", re.IGNORECASE),
    re.compile(r"/page/\d+", re.IGNORECASE),
    re.compile(r"/profile", re.IGNORECASE),
    re.compile(r"/account", re.IGNORECASE),
    re.compile(r"/cabinet", re.IGNORECASE),
    re.compile(r"/interview", re.IGNORECASE),
    re.compile(r"/press", re.IGNORECASE),
    re.compile(r"/banner", re.IGNORECASE),
    re.compile(r"/advertisement", re.IGNORECASE),
    re.compile(r"/rss", re.IGNORECASE),
    re.compile(r"^/ady/", re.IGNORECASE),
    re.compile(r"/pozdravlen", re.IGNORECASE),
    re.compile(r"/auction", re.IGNORECASE),
    re.compile(r"/berezhlivoe", re.IGNORECASE),
    re.compile(r"/korruptsii", re.IGNORECASE),
    re.compile(r"/personal", re.IGNORECASE),
)

SKIP_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "yclid",
    "gclid",
    "page",
    "sort",
    "order",
    "filter",
    "SECTION_ID",
    "ELEMENT_ID",
    "sessid",
    "session_id",
    "token",
    "lang",
    "type",
}
