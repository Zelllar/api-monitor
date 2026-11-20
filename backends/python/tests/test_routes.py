from unittest.mock import patch

def test_get_monitors(client):
    response = client.get("/api/monitors")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_monitor(client):
    response = client.post(
        "/api/monitors",
        json={
            "name": "Test API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test API"
    assert data["url"] == "https://example.com/"
    assert data["intervalSeconds"] == 60
    assert data["isActive"] is True
    assert "id" in data

def test_update_monitor(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Original Name",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/api/monitors/{monitor_id}",
        json={
            "name": "Updated Name"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == monitor_id
    assert data["name"] == "Updated Name"
    assert data["intervalSeconds"] == 60
    assert data["isActive"] is True

def test_update_monitor_not_found(client):
    response = client.patch(
        "/api/monitors/999999",
        json={
            "name": "Updated Name"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Monitor not found"

def test_update_monitor_empty_data(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Test API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/api/monitors/{monitor_id}",
        json={}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "At least one field must be provided"

def test_update_monitor_null_value(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Test API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/api/monitors/{monitor_id}",
        json={
            "name": None
        }
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "name cannot be null"

def test_update_monitor_interval(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Test API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/api/monitors/{monitor_id}",
        json={
            "intervalSeconds": 120
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intervalSeconds"] == 120
    assert data["name"] == "Test API"
    assert data["url"] == "https://example.com/"

def test_update_monitor_url(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Test API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/api/monitors/{monitor_id}",
        json={
            "url": "https://httpbin.org/get"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["url"] == "https://httpbin.org/get"
    assert data["name"] == "Test API"
    assert data["intervalSeconds"] == 60

def test_delete_monitor(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Test API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    response = client.delete(
        f"/api/monitors/{monitor_id}"
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/monitors/{monitor_id}"
    )

    assert get_response.status_code == 404

def test_delete_monitor_not_found(client):
    response = client.delete("/api/monitors/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Monitor not found"

def test_run_monitor_check(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Test API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    with patch("app.routes.check_url") as mock_check:
        mock_check.return_value = {
            "status": "UP",
            "status_code": 200,
            "response_time_ms": 150,
            "error_message": None
        }

        response = client.post(
            f"/api/monitors/{monitor_id}/check"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "UP"
    assert data["statusCode"] == 200
    assert data["responseTimeMs"] == 150
    assert data["errorMessage"] is None

def test_run_monitor_check_not_found(client):
    response = client.post(
        "/api/monitors/999999/check"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Monitor not found"

def test_run_monitor_check_failure(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Failed API",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    with patch("app.routes.check_url") as mock_check:
        mock_check.return_value = {
            "status": "DOWN",
            "status_code": 500,
            "response_time_ms": 200,
            "error_message": None
        }

        response = client.post(
            f"/api/monitors/{monitor_id}/check"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "DOWN"
    assert data["statusCode"] == 500
    assert data["responseTimeMs"] == 200
    assert data["errorMessage"] is None

def test_run_monitor_check_saves_result(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "History Test",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    with patch("app.routes.check_url") as mock_check:
        mock_check.return_value = {
            "status": "UP",
            "status_code": 200,
            "response_time_ms": 120,
            "error_message": None
        }

        client.post(f"/api/monitors/{monitor_id}/check")

    history_response = client.get(
        f"/api/monitors/{monitor_id}/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 1
    assert history[0]["status"] == "UP"
    assert history[0]["statusCode"] == 200
    assert history[0]["responseTimeMs"] == 120

def test_run_monitor_check_failure_saves_result(client):
    create_response = client.post(
        "/api/monitors",
        json={
            "name": "Failed History Test",
            "url": "https://example.com",
            "intervalSeconds": 60
        }
    )

    monitor_id = create_response.json()["id"]

    with patch("app.routes.check_url") as mock_check:
        mock_check.return_value = {
            "status": "DOWN",
            "status_code": 500,
            "response_time_ms": 250,
            "error_message": None
        }

        client.post(f"/api/monitors/{monitor_id}/check")

    history_response = client.get(
        f"/api/monitors/{monitor_id}/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 1
    assert history[0]["status"] == "DOWN"
    assert history[0]["statusCode"] == 500
    assert history[0]["responseTimeMs"] == 250