from __future__ import annotations
from typing import TYPE_CHECKING
import ssl

import httpx

from .ssrf_transport import SSRFGuardTransport

if TYPE_CHECKING:
    from app.core.config import Config


def create_sber_http_client(config: Config) -> httpx.AsyncClient:
    ssl_ctx = ssl.create_default_context(cafile=config.sber_ca_cert_path)
    ssl_ctx.load_cert_chain(
        certfile=config.sber_client_cert_path,
        keyfile=config.sber_client_key_path,
    )

    return create_http_client(config, verify=ssl_ctx)


def create_fetch_client(config: Config) -> httpx.AsyncClient:
    transport = SSRFGuardTransport(verify=True, retries=0)

    return create_http_client(config, transport=transport, timeout=config.fetch_timeout)


def create_http_client(
    config: Config, headers: dict | None = None, *args, **kwargs
) -> httpx.AsyncClient:
    headers = headers or {}

    return httpx.AsyncClient(
        *args, **kwargs, headers={"User-Agent": config.http_user_agent, **headers}
    )
