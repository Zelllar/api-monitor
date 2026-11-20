import httpx
from unittest.mock import patch
from app.checker import check_url


def test_check_url_success():
    with patch("app.checker.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.is_success = True

        result = check_url("https://example.com")

    assert result["status"] == "UP"
    assert result["status_code"] == 200
    assert result["response_time_ms"] >= 0
    assert result["error_message"] is None

def test_check_url_failure():
    with patch("app.checker.httpx.get") as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection failed")

        result = check_url("https://example.com")

    assert result["status"] == "DOWN"
    assert result["status_code"] is None
    assert result["response_time_ms"] >= 0
    assert result["error_message"] == "Connection failed"

def test_check_url_server_error():
    with patch("app.checker.httpx.get") as mock_get:
        mock_get.return_value.status_code = 500
        mock_get.return_value.is_success = False

        result = check_url("https://example.com")

    assert result["status"] == "DOWN"
    assert result["status_code"] == 500
    assert result["response_time_ms"] >= 0
    assert result["error_message"] is None

def test_check_url_timeout():
    with patch("app.checker.httpx.get") as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Request timed out")

        result = check_url("https://example.com")

    assert result["status"] == "DOWN"
    assert result["status_code"] is None
    assert result["response_time_ms"] >= 0
    assert result["error_message"] == "Request timed out"

def test_check_url_request_settings():
    with patch("app.checker.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.is_success = True

        check_url("https://example.com")

    mock_get.assert_called_once_with(
        "https://example.com",
        timeout=10,
        follow_redirects=True
    )