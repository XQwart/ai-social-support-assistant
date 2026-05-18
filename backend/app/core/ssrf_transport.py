import asyncio
import ipaddress
import socket

import httpx

from app.exceptions.fetch_exceptions import UrlSafetyError


class SSRFGuardTransport(httpx.AsyncHTTPTransport):

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url

        if url.scheme not in ("http", "https"):
            raise UrlSafetyError(f"Использован запрещенный протокол {url.scheme}")

        host = url.host
        if not host:
            raise UrlSafetyError("Отсутствует хост")

        ip = await self._resolve_safe_ip(host)

        new_url = url.copy_with(host=ip)

        new_headers = [
            (k, v) for k, v in list(request.headers.raw) if k.lower() != b"host"
        ]
        new_headers.append((b"host", host.encode("ascii")))

        extensions = dict(request.extensions or {})
        extensions["sni_hostname"] = host

        new_request = httpx.Request(
            method=request.method,
            url=new_url,
            headers=new_headers,
            stream=request.stream,
            extensions=extensions,
        )

        return await super().handle_async_request(new_request)

    async def _resolve_safe_ip(self, host: str) -> str:
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            ip = None

        if ip is not None:
            if not self._is_public(ip):
                raise UrlSafetyError(f"Хост {host} является приватным IP {host}")
            return str(ip)

        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise UrlSafetyError("Ошибка при резолве хоста") from exc

        resolved: str | None = None
        for info in infos:
            info_ip = info[4][0]
            try:
                parsed = ipaddress.ip_address(info_ip)
            except ValueError:
                continue
            if not self._is_public(parsed):
                raise UrlSafetyError(f"Хост {host} является приватным IP {info_ip}")

            resolved = str(parsed)

        if not resolved:
            raise UrlSafetyError(f"Не удалось получить ни одного IP для {host}")

        return resolved

    def _is_public(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
