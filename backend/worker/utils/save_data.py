import datetime as dt
import json
from pathlib import Path

from app.core.constants import RAW_DATA_DIR, PROCESSED_DATA_DIR


def save_parsed_data(
    site_name: str, data: list[dict], stage: str = "processed"
) -> Path:
    now = dt.datetime.utcnow()

    if stage == "raw":
        base = RAW_DATA_DIR
    else:
        base = PROCESSED_DATA_DIR

    dir_path = base / site_name / now.strftime("%Y-%m-%d")
    dir_path.mkdir(parents=True, exist_ok=True)

    filename = now.strftime("%H-%M-%S") + ".json"
    file_path = dir_path / filename

    payload = {
        "meta": {
            "site": site_name,
            "parsed_at": now.isoformat(),
            "items_count": len(data),
        },
        "data": data,
    }

    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    return file_path
