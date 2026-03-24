import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: dict | None = None) -> dict:
    if default is None:
        default = []

    try:
        if not path.exists():
            return default

        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return default

        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
