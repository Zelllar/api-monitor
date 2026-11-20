from unittest.mock import patch

import pytest
import httpx
import httpcore
import ssl

from httpcore._backends.sync import SyncBackend
from app.transport import PinnedIPBackend
from unittest.mock import Mock
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone

def create_test_certificate(tmp_path):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "example.com")
    ])

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc).replace(tzinfo=None))
        .not_valid_after(
            (datetime.now(timezone.utc) + timedelta(days=1)).replace(tzinfo=None)
        )
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("example.com")
            ]),
            critical=False
        )
        .sign(private_key, hashes.SHA256())
    )

    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"

    cert_path.write_bytes(
        certificate.public_bytes(serialization.Encoding.PEM)
    )

    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

    return cert_path, key_path

def test_connect_tcp_uses_pinned_ip():
    backend = PinnedIPBackend(
        hostname="example.com",
        ip="93.184.216.34"
    )

    with patch(
        "app.transport.SyncBackend.connect_tcp"
    ) as mock_connect:
        backend.connect_tcp(
            host="example.com",
            port=443
        )

    print(mock_connect.call_args)


def test_connect_tcp_rejects_unexpected_hostname():
    backend = PinnedIPBackend(
        hostname="example.com",
        ip="93.184.216.34"
    )

    with patch(
        "app.transport.SyncBackend.connect_tcp"
    ) as mock_connect:
        with pytest.raises(httpcore.ConnectError):
            backend.connect_tcp(
                host="127.0.0.1",
                port=443
            )

    mock_connect.assert_not_called()

def test_transport_uses_pinned_ip_backend():
    from app.transport import PinnedIPTransport

    transport = PinnedIPTransport(
        hostname="example.com",
        ip="93.184.216.34"
    )

    assert isinstance(
        transport._pool._network_backend,
        PinnedIPBackend
    )

    transport.close()

def test_httpx_client_uses_pinned_transport():
    from app.transport import PinnedIPTransport

    transport = PinnedIPTransport(
        hostname="example.com",
        ip="93.184.216.34"
    )

    with httpx.Client(transport=transport) as client:
        assert client._transport is transport

def test_transport_returns_httpx_response():
    from app.transport import PinnedIPTransport

    transport = PinnedIPTransport(
        hostname="example.com",
        ip="93.184.216.34"
    )

    mock_response = httpcore.Response(
        status=200,
        headers=[(b"content-type", b"text/plain")],
        content=b"OK"
    )

    transport._pool.handle_request = Mock(return_value=mock_response)

    with httpx.Client(transport=transport) as client:
        response = client.get("https://example.com")

    assert response.status_code == 200
    assert response.text == "OK"
    assert response.headers["content-type"] == "text/plain"

class LocalHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass

def start_test_server():
    server = HTTPServer(("127.0.0.1", 0), LocalHTTPHandler)

    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    return server

def start_https_test_server(cert_path, key_path):
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    server_context.load_cert_chain(
        certfile=str(cert_path),
        keyfile=str(key_path)
    )

    server_names = []

    server_context.set_servername_callback(
        lambda sock, server_name, context:
            server_names.append(server_name)
    )

    server = HTTPServer(
        ("127.0.0.1", 0),
        LocalHTTPHandler
    )

    server.socket = server_context.wrap_socket(
        server.socket,
        server_side=True
    )

    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    return server, server_names

def test_transport_sends_request_to_pinned_ip():
    from app.transport import PinnedIPTransport

    server = start_test_server()
    port = server.server_address[1]

    original_connect_tcp = SyncBackend.connect_tcp
    connected_hosts = []

    def recording_connect_tcp(backend, host, *args, **kwargs):
        connected_hosts.append(host)
        return original_connect_tcp(backend, host, *args, **kwargs)

    transport = PinnedIPTransport(
        hostname="localhost",
        ip="127.0.0.1"
    )

    try:
        with patch.object(
            SyncBackend,
            "connect_tcp",
            recording_connect_tcp
        ):
            with httpx.Client(transport=transport) as client:
                response = client.get(f"http://localhost:{port}/")

        assert response.status_code == 200
        assert response.text == "OK"
        assert connected_hosts == ["127.0.0.1"]

    finally:
        server.shutdown()
        server.server_close()

def test_transport_rejects_unexpected_hostname():
    from app.transport import PinnedIPTransport

    transport = PinnedIPTransport(
        hostname="example.com",
        ip="127.0.0.1"
    )

    try:
        with httpx.Client(transport=transport) as client:
            with pytest.raises(httpx.ConnectError):
                client.get("http://localhost/")
    finally:
        transport.close()

def test_transport_preserves_tls_server_name(tmp_path):
    from app.transport import PinnedIPTransport

    cert_path, key_path = create_test_certificate(tmp_path)

    server, server_names = start_https_test_server(
        cert_path,
        key_path
    )

    port = server.server_address[1]

    client_context = ssl.create_default_context(
        cafile=str(cert_path)
    )

    transport = PinnedIPTransport(
        hostname="example.com",
        ip="127.0.0.1",
        ssl_context=client_context
    )

    try:
        with httpx.Client(transport=transport) as client:
            response = client.get(
                f"https://example.com:{port}/"
            )

        assert response.status_code == 200
        assert response.text == "OK"
        assert server_names == ["example.com"]

    finally:
        transport.close()
        server.shutdown()
        server.server_close()