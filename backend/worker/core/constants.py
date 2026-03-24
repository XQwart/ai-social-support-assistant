from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

SOURCES_JSON = DATA_DIR / "sources.json"
FAQ_JSON = DATA_DIR / "faq.json"
CHUCK_JSON = DATA_DIR / "chuck.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
