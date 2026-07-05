from fastapi.testclient import TestClient

from app.main import create_app


def test_readiness_endpoint_returns_safe_flags() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["settings_loaded"] is True
    assert body["checks"]["llm_provider"] == "mock"
    assert body["checks"]["llm_configured"] is True
    assert body["checks"]["live_llm_enabled"] is False


def test_readiness_endpoint_does_not_expose_secret_like_values() -> None:
    client = TestClient(create_app())

    response_text = client.get("/api/v1/readiness").text.lower()

    forbidden_tokens = ("api_key", "password", "secret", "mongodb", "connection", "authorization")
    assert all(token not in response_text for token in forbidden_tokens)

