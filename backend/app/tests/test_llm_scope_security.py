from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]

LLM_FOUNDATION_FILES = (
    APP_DIR / "llm" / "contracts.py",
    APP_DIR / "llm" / "config.py",
    APP_DIR / "llm" / "errors.py",
    APP_DIR / "llm" / "fake_client.py",
    APP_DIR / "llm" / "structured_output.py",
    APP_DIR / "llm" / "redaction.py",
    APP_DIR / "llm" / "retry.py",
)
LIVE_CLIENT_FILE = APP_DIR / "llm" / "live_client.py"
LLM_AGENT_DIR = APP_DIR / "agents" / "llm"

FORBIDDEN_LIVE_REFERENCES = (
    "import httpx",
    "from httpx",
    "import requests",
    "from requests",
    "import openai",
    "from openai",
    "import anthropic",
    "from anthropic",
    "import langchain",
    "from langchain",
    "os.getenv",
    "os.environ",
    "read_text",
    "\".env",
    "'.env",
    "env_file",
    "pymongo",
    "motor",
    "beanie",
)


def test_rebuild_12a_llm_foundation_has_no_live_or_env_access() -> None:
    for path in LLM_FOUNDATION_FILES:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_LIVE_REFERENCES:
            assert forbidden not in text, f"{path.name} references forbidden {forbidden}"


def test_routes_repositories_and_orchestration_do_not_import_llm_clients() -> None:
    checked_dirs = (
        APP_DIR / "api",
        APP_DIR / "repositories",
        APP_DIR / "orchestration",
    )
    for directory in checked_dirs:
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "app.llm" not in text, f"{path} imports app.llm"


def test_only_controlled_llm_agent_imports_llm_clients_in_rebuild_12c() -> None:
    allowed = {path.resolve() for path in LLM_AGENT_DIR.rglob("*.py")}
    for path in (APP_DIR / "agents").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "app.llm" in text:
            assert path.resolve() in allowed, f"{path} imports app.llm outside 12C agent"


def test_live_client_boundary_has_no_env_file_or_product_coupling() -> None:
    text = LIVE_CLIENT_FILE.read_text(encoding="utf-8").lower()

    assert "read_text" not in text
    assert "\".env" not in text
    assert "'.env" not in text
    assert "env_file" not in text
    assert "app.agents" not in text
    assert "app.api" not in text
    assert "app.repositories" not in text
    assert "app.orchestration" not in text
