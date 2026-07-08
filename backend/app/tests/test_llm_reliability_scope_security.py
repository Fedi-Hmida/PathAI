from __future__ import annotations

from pathlib import Path

from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.mock import MockKnowledgeMapAgent
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient, FakeLLMScenario, LLMRetryPolicy
from app.llm.observability.sinks import CountingObserver
from app.schemas.knowledge_map import KnowledgeMapAgentInput

AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"
LLM_AGENT_DIR = AGENTS_DIR / "llm"
LLM_AGENT_FILES = (
    LLM_AGENT_DIR / "assessment.py",
    LLM_AGENT_DIR / "critic.py",
    LLM_AGENT_DIR / "curriculum.py",
    LLM_AGENT_DIR / "knowledge_map.py",
)

_FORBIDDEN_EVENT_CONTENT_PATTERNS = ("str(exc)", "exc.args", ".raw_text", "request.prompt")


def test_agent_files_never_pass_dynamic_content_into_reliability_events() -> None:
    for path in LLM_AGENT_FILES:
        text = path.read_text(encoding="utf-8")
        for forbidden in _FORBIDDEN_EVENT_CONTENT_PATTERNS:
            assert forbidden not in text, f"{path.name} references forbidden {forbidden}"


def test_agent_files_only_use_fixed_reason_codes() -> None:
    allowed = {"fallback_to_deterministic"}
    for path in LLM_AGENT_FILES:
        text = path.read_text(encoding="utf-8")
        occurrences = text.count("reason_code=")
        assert occurrences >= 1, f"{path.name} should record at least one reason_code"
        for allowed_value in allowed:
            assert f'reason_code="{allowed_value}"' in text


def test_only_llm_agent_directory_imports_app_llm_after_15d() -> None:
    for path in AGENTS_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "app.llm" in text:
            assert LLM_AGENT_DIR in path.parents, f"{path} imports app.llm outside app/agents/llm/"


def test_api_repositories_orchestration_still_import_no_app_llm() -> None:
    app_dir = AGENTS_DIR.parent
    checked_dirs = (app_dir / "api", app_dir / "repositories", app_dir / "orchestration")
    for directory in checked_dirs:
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "app.llm" not in text, f"{path} imports app.llm"


def test_fallback_event_error_code_contains_only_known_safe_values() -> None:
    # retry.py's own ATTEMPT_FAILED/RETRY_EXHAUSTED events (15B) carry the
    # original failure's tag ("llm_provider_error"). By the time the agent's
    # `except LLMError` catches it, retry.py has already wrapped it as
    # `LLMRetryLimitExceeded` — so the agent-level FALLBACK_USED event's
    # error_code is that wrapper's own tag, not the original cause. Both are
    # fixed, known, class-level tags; neither is ever raw exception text.
    observer = CountingObserver()

    llm_agent = LLMKnowledgeMapAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
        retry_policy=LLMRetryPolicy(max_attempts=1, backoff_seconds=0),
        observer=observer,
    )

    llm_agent.build_knowledge_map(_knowledge_map_input())

    summary = observer.safe_summary()
    assert summary["counts_by_error_code"] == {
        "llm_provider_error": 2,
        "llm_retry_limit_exceeded": 1,
    }


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )
