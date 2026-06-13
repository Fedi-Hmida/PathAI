from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def build_app(**overrides: object) -> FastAPI:
    settings_cls = cast(Any, Settings)
    settings = cast(Settings, settings_cls(
        _env_file=None,
        mongodb_connect_on_startup=False,
        **overrides,
    ))
    return create_app(settings)


def test_dev_endpoints_are_blocked_when_disabled() -> None:
    app = build_app(enable_dev_endpoints=False)

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/models")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "dev_endpoints_disabled"


def test_demo_endpoints_are_blocked_when_disabled_but_health_remains_open() -> None:
    app = build_app(enable_demo_endpoints=False)

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        response = client.post(
            "/api/v1/evaluation/learning-gain",
            json={"pre_test_score": 40, "post_test_score": 70, "max_score": 100},
        )

    assert health.status_code == 200
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "demo_endpoints_disabled"


def test_rate_limit_middleware_blocks_after_configured_threshold() -> None:
    app = build_app(rate_limit_enabled=True, rate_limit_requests_per_minute=1)

    with TestClient(app) as client:
        first = client.get("/api/v1/health")
        second = client.get("/api/v1/health")

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limit_exceeded"


def test_request_id_and_security_headers_are_added() -> None:
    app = build_app()

    with TestClient(app) as client:
        response = client.get("/api/v1/health", headers={"X-Request-ID": "req_known"})

    assert response.headers["X-Request-ID"] == "req_known"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_cors_allows_configured_local_origin() -> None:
    app = build_app(allowed_origins=["http://localhost:3000"])

    with TestClient(app) as client:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_production_like_errors_hide_internal_exception_details() -> None:
    app = build_app(app_env="production")

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("internal secret failure")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["message"] == "Internal server error."
    assert "internal secret failure" not in str(payload)


def test_no_authentication_modules_were_added() -> None:
    forbidden_module_names = {"auth.py", "jwt.py", "passwords.py", "sessions.py", "users.py"}
    security_files = {path.name for path in Path("app/security").glob("*.py")}

    assert security_files.isdisjoint(forbidden_module_names)
