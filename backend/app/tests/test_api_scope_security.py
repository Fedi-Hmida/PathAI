from __future__ import annotations

from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1] / "api" / "v1"
API_MODULES = [
    "adaptation.py",
    "assessment.py",
    "auth.py",
    "critic.py",
    "curriculum.py",
    "dashboard.py",
    "demo.py",
    "dependencies.py",
    "errors.py",
    "evaluation.py",
    "goal.py",
    "knowledge_map.py",
    "orchestration.py",
    "progress.py",
    "quiz.py",
    "resource.py",
    "router.py",
    "workspace.py",
]
ROUTE_MODULES = [
    module
    for module in API_MODULES
    if module not in {"dependencies.py", "errors.py", "router.py"}
]
FORBIDDEN_BOUNDARY_IMPORTS = (
    "app.llm",
    "app.agents",
    "app.orchestration.graph",
    "langgraph",
    "motor",
    "pymongo",
    "beanie",
    "requests",
    "httpx",
    "frontend",
)


def test_api_modules_do_not_import_forbidden_runtime_boundaries() -> None:
    for module in API_MODULES:
        text = (API_DIR / module).read_text(encoding="utf-8").lower()
        assert ".env" not in text
        for forbidden in FORBIDDEN_BOUNDARY_IMPORTS:
            assert forbidden not in text, f"{module} imports or references {forbidden}"


def test_route_modules_do_not_import_repositories_directly() -> None:
    for module in ROUTE_MODULES:
        text = (API_DIR / module).read_text(encoding="utf-8")
        assert "app.repositories" not in text, f"{module} should call services only"
