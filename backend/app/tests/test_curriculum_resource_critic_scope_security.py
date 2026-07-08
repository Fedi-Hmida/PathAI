from __future__ import annotations

from pathlib import Path

FILES_TO_SCAN = (
    Path("app/agents/deterministic/curriculum.py"),
    Path("app/agents/deterministic/resource.py"),
    Path("app/agents/deterministic/critic.py"),
    Path("app/agents/mock/curriculum.py"),
    Path("app/agents/mock/resource.py"),
    Path("app/agents/mock/critic.py"),
    Path("app/agents/services/curriculum.py"),
    Path("app/agents/services/resource.py"),
    Path("app/agents/services/critic.py"),
    Path("app/orchestration/nodes.py"),
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
    "frontend",
)


def test_curriculum_resource_critic_scope_has_no_forbidden_coupling() -> None:
    for path in FILES_TO_SCAN:
        source = path.read_text(encoding="utf-8").lower()
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in source, f"{pattern} found in {path}"
