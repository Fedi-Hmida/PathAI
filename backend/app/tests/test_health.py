from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_safe_ok_payload() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "PathAI",
        "environment": "local",
    }

