from __future__ import annotations

import json
from pathlib import Path


def read_json_file(path: str | Path) -> list[dict]:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Ожидался список объектов в JSON")

    return data
