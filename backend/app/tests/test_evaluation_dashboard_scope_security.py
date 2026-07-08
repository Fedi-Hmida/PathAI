from __future__ import annotations

from pathlib import Path

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.runner import run_straight_line_demo_from_container

APP_DIR = Path(__file__).resolve().parents[1]

REBUILD_11_FILES = (
    APP_DIR / "agents" / "deterministic" / "evaluation.py",
    APP_DIR / "agents" / "mock" / "evaluation.py",
    APP_DIR / "agents" / "services" / "evaluation.py",
    APP_DIR / "services" / "dashboard.py",
    APP_DIR / "services" / "reporting.py",
    APP_DIR / "schemas" / "dashboard.py",
    APP_DIR / "schemas" / "reporting.py",
    APP_DIR / "orchestration" / "nodes.py",
)

FORBIDDEN_REFERENCES = (
    ".env",
    "app.llm",
    "beanie",
    "docker",
    "fastapi",
    "frontend",
    "httpx",
    "jwt",
    "langchain",
    "mongodb",
    "motor",
    "openai",
    "pymongo",
    "requests",
)


def test_rebuild_11_modules_do_not_reference_forbidden_boundaries() -> None:
    for path in REBUILD_11_FILES:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_REFERENCES:
            assert forbidden not in text, f"{path.name} references forbidden {forbidden}"


def test_dashboard_and_reporting_outputs_are_answer_key_safe() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)
    dashboard = container.dashboard_service.get_by_run_id(result.run.run_id)
    reporting = container.reporting_service.get_summary_by_run_id(result.run.run_id)

    combined = (
        dashboard.model_dump_json().lower()
        + reporting.model_dump_json().lower()
        + str(result.state.model_dump()).lower()
    )

    assert "correct_answer" not in combined
    assert "selected_options" not in combined
    assert "question_quiz" not in combined
    assert "dashboardpayload" not in combined
    assert "reportingsummary" not in combined
    assert "traceback" not in combined
    assert "secret" not in combined
