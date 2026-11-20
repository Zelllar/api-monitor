import time
import httpx
import ipaddress
import socket
from urllib.parse import urlparse
from app.transport import PinnedIPTransport

REQUEST_TIMEOUT = 10

def is_public_ip(ip: str) -> bool:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False

    return address.is_global

def is_safe_url(url: str) -> list[str] | None:
    try:
        parsed_url = urlparse(url)
    except ValueError:
        return None

    if parsed_url.scheme not in ("http", "https"):
        return None

    hostname = parsed_url.hostname

    if not hostname:
        return None

    if parsed_url.username or parsed_url.password:
        return None

    try:
        parsed_url.port
    except ValueError:
        return None

    try:
        ip_addresses = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM
        )

        if not ip_addresses:
            return None

        public_ips = []

        for address in ip_addresses:
            ip = address[4][0]

            if not is_public_ip(ip):
                return None

            public_ips.append(ip)

        return public_ips

    except socket.gaierror:
        return None

def check_url(url: str) -> dict:
    start_time = time.perf_counter()
    ip_addresses = is_safe_url(url)

    if ip_addresses is None:
        return {
            "status": "DOWN",
            "status_code": None,
            "response_time_ms": 0,
            "error_message": "Unsafe URL"
        }

    try:
        with httpx.Client(
            transport=PinnedIPTransport(
                hostname=urlparse(url).hostname,
                ip=ip_addresses[0]
            ),
            timeout=REQUEST_TIMEOUT,
            follow_redirects=False
        ) as client:
            response = client.get(url)

        response_time = time.perf_counter() - start_time

        return {
            "status": "UP" if response.is_success else "DOWN",
            "status_code": response.status_code,
            "response_time_ms": round(response_time * 1000),
            "error_message": None
        }

    except Exception as error:
        response_time = time.perf_counter() - start_time

        return {
            "status": "DOWN",
            "status_code": None,
            "response_time_ms": round(response_time * 1000),
            "error_message": str(error)
        }