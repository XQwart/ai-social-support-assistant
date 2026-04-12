from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CERT_DIR = BASE_DIR / "cert"
DATA_DIR = BASE_DIR / "data"

FAQ_JSON = DATA_DIR / "faq.json"
CHUCK_JSON = DATA_DIR / "chuck.json"
