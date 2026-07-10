from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.fixtures import canonical_demo as demo
from app.main import create_app
from app.repositories.errors import RepositoryError
from app.services.curriculum import CurriculumService
from app.services.orchestration_run import OrchestrationRunService


def test_post_orchestration_runs_returns_200_and_failed_status_on_node_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_api_container_for_tests()

    def _raise(_self: CurriculumService, _curriculum_id: str) -> None:
        raise RuntimeError("stubbed failure for Rebuild-18E, must never reach the client")

    # context.curricula (OrchestrationContext.from_container) is the exact
    # same object as container.curriculum_service -- load_curriculum builds
    # its own curriculum via the agent service and succeeds; load_resources
    # is the first node to read it back via get_by_id, so it is the one that
    # fails, proving a mid-pipeline (not first-node) failure is handled too.
    # CurriculumService is a slots dataclass, so the patch targets the class,
    # not the instance.
    monkeypatch.setattr(CurriculumService, "get_by_id", _raise)

    client = TestClient(create_app())
    response = client.post("/api/v1/orchestration/runs")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "load_resources" in body["failed_nodes"]
    assert "load_curriculum" in body["completed_nodes"]
    assert "load_resources" not in body["completed_nodes"]
    assert len(body["errors"]) == 1
    assert body["errors"][0]["error_code"] == "orchestration_node_failed"

    response_text = response.text
    for forbidden in (
        "RuntimeError",
        "stubbed failure",
        "Traceback",
        "site-packages",
        ".py\", line",
    ):
        assert forbidden not in response_text

    # The persisted FAILED run is the same one a caller would read via GET.
    get_response = client.get(f"/api/v1/orchestration/runs/{demo.RUN_ID}")
    assert get_response.status_code == 200
    assert get_response.json() == body


def test_unexpected_repository_error_still_maps_through_existing_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_api_container_for_tests()

    def _raise(_self: OrchestrationRunService, _run_id: str) -> None:
        raise RepositoryError("stubbed repository boundary failure")

    # A failure inside orchestration_run_service.get_by_id happens outside
    # run_node's try/except (it is used by _mark_node_completed itself, and
    # by initialize_run's create-or-get path), so it propagates as a genuine
    # unhandled-at-the-node-level error, exercised via the pre-existing
    # RepositoryError -> 500 handler in app/api/v1/errors.py, not a new one.
    monkeypatch.setattr(OrchestrationRunService, "get_by_id", _raise)

    client = TestClient(create_app())
    response = client.post("/api/v1/orchestration/runs")

    assert response.status_code == 500
    assert response.json() == {"detail": "repository boundary error"}
