from __future__ import annotations

from pathlib import Path

FILES_TO_SCAN = (
    Path("app/agents/deterministic/assessment.py"),
    Path("app/agents/deterministic/knowledge_map.py"),
    Path("app/agents/mock/assessment.py"),
    Path("app/agents/mock/knowledge_map.py"),
    Path("app/agents/services/assessment.py"),
    Path("app/agents/services/knowledge_map.py"),
)

FORBIDDEN_PATTERNS = (
    ".env",
    "pymongo",
    "motor",
    "beanie",
    "requests",
    "httpx",
    "openai",
    "anthropic",
    "langchain",
    "mongodb://",
    "jwt",
    "docker",
)


def test_assessment_knowledge_map_scope_has_no_forbidden_coupling() -> None:
    for path in FILES_TO_SCAN:
        source = path.read_text(encoding="utf-8").lower()
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in source, f"{pattern} found in {path}"
