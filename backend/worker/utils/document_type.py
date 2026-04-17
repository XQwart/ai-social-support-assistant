from __future__ import annotations

from urllib.parse import urlparse

from worker.core.constants import DOCUMENT_EXTENSIONS


def detect_document_type(url: str) -> str:
    path = urlparse(url).path.lower()

    for ext in DOCUMENT_EXTENSIONS:
        if path.endswith(ext):
            return ext.removeprefix(".")

    return "html"
