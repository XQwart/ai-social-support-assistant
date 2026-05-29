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


def build_source_jobs(sources: list[dict]) -> list[dict]:
    jobs: list[dict] = []

    for item in sources:
        region_name = None
        region_code = None

        region_name_raw = item.get("region")
        region_code_raw = item.get("code")

        if region_name_raw is not None and region_code_raw is not None:
            normalized_name = str(region_name_raw).strip()
            normalized_code = str(region_code_raw).strip().zfill(2)

            if normalized_name and normalized_code:
                region_name = normalized_name
                region_code = normalized_code

        for source_item in item.get("sources", []):
            jobs.append(
                {
                    "url": source_item["url"],
                    "place_of_work": source_item.get("place_of_work"),
                    "region_name": region_name,
                    "region_code": region_code,
                }
            )

    return jobs
