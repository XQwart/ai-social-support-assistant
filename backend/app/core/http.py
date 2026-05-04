from __future__ import annotations
from typing import TYPE_CHECKING
import ssl
import socket
import ipaddress
from urllib.parse import urlparse

import httpx

from app.exceptions.fetch_exceptions import UrlSafetyError

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
    return create_http_client(config, event_hooks={"request": [_ssrf_hook]})


def _ssrf_hook(url: str) -> None:
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise UrlSafetyError(f"Ошибка при парсе ссылки") from exc

    if parsed.scheme not in ("http", "https"):
        raise UrlSafetyError(f"Использован запрещенный протокол {parsed.scheme}")

    host = parsed.hostname
    if not host:
        raise UrlSafetyError("Отсутствует хост")

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UrlSafetyError("Ошибка при резолве хоста")

    for info in infos:
        info_ip = info[4][0]
        try:
            ip = ipaddress.ip_address(info_ip)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UrlSafetyError(f"Хост {host} является приватным ip {info_ip}")


def create_http_client(
    config: Config, headers: dict = {}, *args, **kwargs
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        *args, **kwargs, headers={"User-Agent": config.http_user_agent, **headers}
    )
