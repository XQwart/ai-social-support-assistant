import ipaddress
import socket

from langchain_core.tools import tool


@tool
def fetch_page(url: str) -> str:  # Заглушка
    """Инструмент для парсинга веб-страницы"""

    return "Инструмент временно недоступен."


def _is_safe_host(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
    except (socket.gaierror, ValueError):
        return False

    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
