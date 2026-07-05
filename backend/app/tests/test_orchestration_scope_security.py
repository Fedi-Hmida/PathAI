from __future__ import annotations

from pathlib import Path

ORCHESTRATION_DIR = Path(__file__).resolve().parents[1] / "orchestration"
ORCHESTRATION_MODULES = [
    "__init__.py",
    "errors.py",
    "events.py",
    "graph.py",
    "nodes.py",
    "runner.py",
    "state.py",
]
FORBIDDEN_REFERENCES = (
    ".env",
    "app.api",
    "app.llm",
    "auth",
    "beanie",
    "docker",
    "frontend",
    "httpx",
    "mongodb",
    "motor",
    "pymongo",
    "requests",
)
FORBIDDEN_REPOSITORY_IMPORTS = (
    "app.repositories.fakes",
    "app.repositories.protocols",
    "app.agents.mock",
)


def test_orchestration_modules_do_not_reference_forbidden_boundaries() -> None:
    for module in ORCHESTRATION_MODULES:
        text = (ORCHESTRATION_DIR / module).read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_REFERENCES:
            assert forbidden not in text, f"{module} references forbidden boundary {forbidden}"


def test_orchestration_nodes_do_not_construct_repositories_directly() -> None:
    for module in ORCHESTRATION_MODULES:
        text = (ORCHESTRATION_DIR / module).read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_REPOSITORY_IMPORTS:
            assert forbidden not in text, f"{module} imports repository implementation {forbidden}"
