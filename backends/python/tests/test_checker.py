import httpx
import pytest

from unittest.mock import patch, ANY
from app.checker import check_url, is_public_ip, is_safe_url
from app.transport import PinnedIPTransport

def test_check_url_success():
    with patch("app.checker.httpx.Client") as mock_client:
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.status_code = 200
        mock_response.is_success = True

        result = check_url("https://example.com")

    assert result["status"] == "UP"
    assert result["status_code"] == 200
    assert result["response_time_ms"] >= 0
    assert result["error_message"] is None

def test_check_url_failure():
    with patch("app.checker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = (
            httpx.ConnectError("Connection failed")
        )

        result = check_url("https://example.com")

    assert result["status"] == "DOWN"
    assert result["status_code"] is None
    assert result["response_time_ms"] >= 0
    assert result["error_message"] == "Connection failed"

def test_check_url_server_error():
    with patch("app.checker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value.status_code = 500
        mock_client.return_value.__enter__.return_value.get.return_value.is_success = False

        result = check_url("https://example.com")

    assert result["status"] == "DOWN"
    assert result["status_code"] == 500
    assert result["response_time_ms"] >= 0
    assert result["error_message"] is None

def test_check_url_timeout():
    with patch("app.checker.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = (
            httpx.TimeoutException("Request timed out")
        )

        result = check_url("https://example.com")

    assert result["status"] == "DOWN"
    assert result["status_code"] is None
    assert result["response_time_ms"] >= 0
    assert result["error_message"] == "Request timed out"

def test_check_url_request_settings():
    with patch("app.checker.is_safe_url", return_value=["93.184.216.34"]):
        with patch("app.checker.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value.status_code = 200
            mock_client.return_value.__enter__.return_value.get.return_value.is_success = True

            check_url("https://example.com")

    mock_client.assert_called_once_with(
        transport=ANY,
        timeout=10,
        follow_redirects=False
    )

    mock_client.return_value.__enter__.return_value.get.assert_called_once_with(
        "https://example.com"
    )

def test_is_public_ip_accepts_public_ipv4():
    assert is_public_ip("8.8.8.8") is True

def test_is_public_ip_rejects_private_ipv4():
    assert is_public_ip("192.168.1.1") is False

def test_is_public_ip_accepts_public_ipv6():
    assert is_public_ip("2001:4860:4860::8888") is True

def test_is_public_ip_rejects_private_ipv6():
    assert is_public_ip("fc00::1") is False

def test_is_public_ip_rejects_invalid_ip():
    assert is_public_ip("not-an-ip") is False

def test_is_safe_url_accepts_public_ip():
    assert is_safe_url("https://8.8.8.8") == ["8.8.8.8"]

def test_is_safe_url_rejects_private_ip():
    assert is_safe_url("http://192.168.1.1") is None

def test_is_safe_url_rejects_mixed_public_and_private_ips():
    from unittest.mock import patch

    with patch("app.checker.socket.getaddrinfo") as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("8.8.8.8", 443)),
            (2, 1, 6, "", ("192.168.1.1", 443)),
        ]

        assert is_safe_url("https://example.com") is None

def test_is_safe_url_rejects_unsupported_scheme():
    assert is_safe_url("ftp://example.com") is None

def test_is_safe_url_rejects_missing_hostname():
    assert is_safe_url("https:///") is None

def test_is_safe_url_rejects_credentials():
    assert is_safe_url("https://user:password@example.com") is None

def test_is_safe_url_rejects_invalid_port():
    assert is_safe_url("https://example.com:99999") is None

def test_is_safe_url_rejects_dns_error():
    from unittest.mock import patch
    import socket

    with patch("app.checker.socket.getaddrinfo") as mock_getaddrinfo:
        mock_getaddrinfo.side_effect = socket.gaierror

        assert is_safe_url("https://nonexistent.example") is None

def test_is_safe_url_rejects_invalid_url():
    assert is_safe_url("https://[invalid-ip]") is None

def test_is_safe_url_rejects_empty_dns_result():
    from unittest.mock import patch

    with patch("app.checker.socket.getaddrinfo") as mock_getaddrinfo:
        mock_getaddrinfo.return_value = []

        assert is_safe_url("https://example.com") is None

@pytest.mark.parametrize("status_code", [301, 302, 303, 307, 308])

def test_check_url_does_not_follow_redirects(status_code):
    with patch("app.checker.is_safe_url", return_value=["93.184.216.34"]):
        with patch("app.checker.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value.status_code = status_code
            mock_client.return_value.__enter__.return_value.get.return_value.is_success = False

            result = check_url("https://example.com")

    assert result["status"] == "DOWN"
    assert result["status_code"] == status_code

    mock_client.return_value.__enter__.return_value.get.assert_called_once_with(
        "https://example.com"
    )

    mock_client.assert_called_once_with(
        transport=ANY,
        timeout=10,
        follow_redirects=False
    )

def test_check_url_uses_pinned_ip_transport():
    with patch(
        "app.checker.is_safe_url",
        return_value=["93.184.216.34"]
    ):
        with patch(
            "app.checker.PinnedIPTransport"
        ) as mock_transport:
            with patch("app.checker.httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.return_value.status_code = 200
                mock_client.return_value.__enter__.return_value.get.return_value.is_success = True

                check_url("https://example.com")

    mock_transport.assert_called_once_with(
        hostname="example.com",
        ip="93.184.216.34"
    )

    mock_client.assert_called_once_with(
        transport=mock_transport.return_value,
        timeout=10,
        follow_redirects=False
    )