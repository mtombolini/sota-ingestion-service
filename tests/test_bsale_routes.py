from fastapi.testclient import TestClient

from app.api import create_app


def test_cannot_enable_real_mode_without_credentials() -> None:
    client = TestClient(create_app())

    response = client.patch("/connectors/bsale", json={"mode": "real", "check_connection": False})

    assert response.status_code == 400
    assert "api_key" in response.json()["detail"]


def test_can_switch_to_real_mode_and_attempt_connection() -> None:
    client = TestClient(create_app())

    response = client.patch(
        "/connectors/bsale",
        json={
            "mode": "real",
            "base_url": "https://api.bsale.io/v1",
            "api_key": "demo-token-1234",
            "check_connection": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "real"
    assert payload["base_url"] == "https://api.bsale.io/v1"
    assert payload["api_key"].endswith("1234")
