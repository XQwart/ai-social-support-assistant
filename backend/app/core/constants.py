from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CERT_DIR = BASE_DIR / "cert"
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

SOURCES_JSON = DATA_DIR / "sources.json"
FAQ_JSON = DATA_DIR / "faq.json"
CHUCK_JSON = DATA_DIR / "chuck.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
