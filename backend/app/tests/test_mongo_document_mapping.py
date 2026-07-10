from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.orchestration import OrchestrationRunDTO

APP_DIR = Path(__file__).resolve().parents[1]
BOUNDARY_DIRS = ("api", "agents", "orchestration", "services")

_ORCHESTRATION_RUN = OrchestrationRunDTO(
    run_id="run_mapping_test",
    goal_id="goal_mapping_test",
    workflow_version="demo-v1",
    status=OrchestrationRunStatus.IN_PROGRESS,
    current_node="load_curriculum",
    completed_nodes=["goal_loaded"],
    failed_nodes=[],
    node_events=[],
    artifact_ids={"goal_id": "goal_mapping_test"},
    started_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
    completed_at=None,
    created_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
    updated_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
)


def test_learning_goal_document_round_trip() -> None:
    document = to_document(demo.LEARNING_GOAL, demo.LEARNING_GOAL.goal_id)

    assert document["_id"] == demo.LEARNING_GOAL.goal_id
    assert document["goal_id"] == demo.LEARNING_GOAL.goal_id
    assert document["status"] == demo.LEARNING_GOAL.status.value
    assert isinstance(document["created_at"], str)

    restored = from_document(document, type(demo.LEARNING_GOAL))
    assert restored == demo.LEARNING_GOAL


def test_orchestration_run_document_round_trip() -> None:
    document = to_document(_ORCHESTRATION_RUN, _ORCHESTRATION_RUN.run_id)

    assert document["_id"] == _ORCHESTRATION_RUN.run_id
    assert document["status"] == _ORCHESTRATION_RUN.status.value
    assert document["completed_nodes"] == ["goal_loaded"]

    restored = from_document(document, OrchestrationRunDTO)
    assert restored == _ORCHESTRATION_RUN


def test_mongo_repositories_package_is_not_imported_outside_its_own_scope() -> None:
    for boundary_dir in BOUNDARY_DIRS:
        directory = APP_DIR / boundary_dir
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "app.repositories.mongo" not in text, (
                f"{path} references app.repositories.mongo, which is not wired in yet"
            )
