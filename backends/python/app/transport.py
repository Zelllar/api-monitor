import typing
import httpx
import httpcore
import ssl

from httpcore._backends.sync import SyncBackend
from httpx._transports.default import map_httpcore_exceptions
from httpx._transports.default import ResponseStream


class PinnedIPBackend(SyncBackend):
    def __init__(self, hostname: str, ip: str):
        self.hostname = hostname
        self.ip = ip

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options=None
    ):
        if host.lower() != self.hostname.lower():
            raise httpcore.ConnectError("Unexpected hostname")

        return super().connect_tcp(
            self.ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options
        )

class PinnedIPTransport(httpx.BaseTransport):
    def __init__(
        self,
        hostname: str,
        ip: str,
        ssl_context: ssl.SSLContext | None = None
    ):
        self._pool = httpcore.ConnectionPool(
            ssl_context=ssl_context,
            network_backend=PinnedIPBackend(hostname, ip)
        )

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        assert isinstance(request.stream, httpx.SyncByteStream)

        req = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )

        with map_httpcore_exceptions():
            resp = self._pool.handle_request(req)

        assert isinstance(resp.stream, typing.Iterable)

        return httpx.Response(
            status_code=resp.status,
            headers=resp.headers,
            stream=ResponseStream(resp.stream),
            extensions=resp.extensions,
        )

    def close(self) -> None:
        self._pool.close()