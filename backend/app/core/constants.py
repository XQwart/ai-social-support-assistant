from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent[2]
CERT_DIR = BASE_DIR / "cert"

DATA_DIR = BASE_DIR / "data"
SOURCE_DIR = DATA_DIR / "source"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
