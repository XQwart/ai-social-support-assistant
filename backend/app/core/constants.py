from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CERT_DIR = BASE_DIR / "cert"
DATA_DIR = BASE_DIR / "data"

FAQ_JSON = DATA_DIR / "faq.json"
CHUCK_JSON = DATA_DIR / "chuck.json"

SBER_EMPLOYEE_PLACE_OF_WORK = "ПАО Сбербанк"


def is_sber_employee_place_of_work(place_of_work: str | None) -> bool:
    if not place_of_work:
        return False
    return place_of_work.strip().casefold() == SBER_EMPLOYEE_PLACE_OF_WORK.casefold()
