from __future__ import annotations

from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"
ORCHESTRATION_DIR = Path(__file__).resolve().parents[1] / "orchestration"
FORBIDDEN_REFERENCES = (
    ".env",
    "app.api.v1",
    "app.llm",
    "beanie",
    "docker",
    "frontend",
    "httpx",
    "mongodb",
    "motor",
    "pymongo",
    "requests",
)
FORBIDDEN_ORCHESTRATION_REFERENCES = (
    "app.agents.mock",
    "app.agents.contracts",
)


def test_agent_modules_do_not_reference_forbidden_boundaries() -> None:
    for path in AGENTS_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_REFERENCES:
            if forbidden == "app.llm" and _is_controlled_llm_agent_file(path):
                continue
            assert forbidden not in text, f"{path.name} references forbidden {forbidden}"


def test_orchestration_uses_agent_services_only() -> None:
    for path in ORCHESTRATION_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_ORCHESTRATION_REFERENCES:
            assert forbidden not in text, f"{path.name} references forbidden {forbidden}"


def _is_controlled_llm_agent_file(path: Path) -> bool:
    return (AGENTS_DIR / "llm") in path.parents
