from __future__ import annotations

from pathlib import Path

from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import Settings, get_settings
from app.fixtures import canonical_demo as demo
from app.orchestration.nodes import NODE_SEQUENCE
from app.schemas.enums import OrchestrationRunStatus


def test_run_demo_pipeline_completes_and_returns_populated_run() -> None:
    get_settings.cache_clear()
    container = ApiServiceContainer()

    run = container.run_demo_pipeline()

    assert run.status == OrchestrationRunStatus.COMPLETED
    assert run.run_id == demo.RUN_ID
    assert run.goal_id == demo.GOAL_ID
    assert list(run.completed_nodes) == list(NODE_SEQUENCE)
    assert run.failed_nodes == []
    assert run.artifact_ids["goal_id"] == demo.GOAL_ID


def test_enable_orchestration_run_route_defaults_true_and_is_not_redacted() -> None:
    settings = Settings()

    assert settings.enable_orchestration_run_route is True
    assert settings.redacted_dict()["enable_orchestration_run_route"] is True


def test_only_orchestration_route_module_reaches_the_trigger() -> None:
    # As of Rebuild-18B, orchestration.py is the sole intended caller of
    # run_demo_pipeline (POST /orchestration/runs). Every other route module
    # must still have no path to the trigger.
    api_dir = Path(__file__).resolve().parents[1] / "api" / "v1"
    route_modules_without_trigger = [
        "adaptation.py",
        "assessment.py",
        "critic.py",
        "curriculum.py",
        "dashboard.py",
        "demo.py",
        "evaluation.py",
        "goal.py",
        "knowledge_map.py",
        "progress.py",
        "quiz.py",
        "resource.py",
    ]
    for module in route_modules_without_trigger:
        text = (api_dir / module).read_text(encoding="utf-8")
        assert "run_demo_pipeline" not in text, f"{module} should not reach the trigger"

    orchestration_text = (api_dir / "orchestration.py").read_text(encoding="utf-8")
    assert "run_demo_pipeline" in orchestration_text

    router_text = (api_dir / "router.py").read_text(encoding="utf-8")
    assert "run_demo_pipeline" not in router_text
