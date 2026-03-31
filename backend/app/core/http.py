from __future__ import annotations
from typing import TYPE_CHECKING
import ssl

import httpx

if TYPE_CHECKING:
    from app.core.config import Config


def create_sber_http_client(config: Config) -> httpx.AsyncClient:
    ssl_ctx = ssl.create_default_context(cafile=config.sber_ca_cert_path)
    ssl_ctx.load_cert_chain(
        certfile=config.sber_client_cert_path,
        keyfile=config.sber_client_key_path,
    )

    return httpx.AsyncClient(verify=ssl_ctx)
