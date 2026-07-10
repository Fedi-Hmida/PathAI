import os
from typing import cast

import pytest

from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.mock.knowledge_map import MockKnowledgeMapAgent
from app.core.settings import Settings
from app.fixtures import canonical_demo as demo
from app.llm.live_client import LIVE_LLM_OPT_IN_ENV_VAR, build_live_client_from_settings
from app.llm.observability.sinks import CountingObserver
from app.schemas.assessment import ConceptEvidence
from app.schemas.knowledge_map import KnowledgeMapAgentInput

pytestmark = pytest.mark.skipif(
    os.getenv(LIVE_LLM_OPT_IN_ENV_VAR, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live LLM agent checks are optional and require "
        f"{LIVE_LLM_OPT_IN_ENV_VAR}=1."
    ),
)


def _live_settings_or_skip() -> Settings:
    settings = Settings()
    try:
        build_live_client_from_settings(settings)
    except RuntimeError as exc:
        pytest.skip(str(exc))
    return settings


@pytest.mark.live_llm
def test_live_knowledge_map_agent_calls_real_provider_without_falling_back() -> None:
    settings = _live_settings_or_skip()
    client = build_live_client_from_settings(settings)
    observer = CountingObserver()
    agent = LLMKnowledgeMapAgent(
        client=client,
        fallback_agent=MockKnowledgeMapAgent(),
        observer=observer,
    )

    payload = KnowledgeMapAgentInput(
        goal_text="Learn the fundamentals of distributed systems.",
        assessment_answers=[demo.ASSESSMENT_ANSWERS[0]],
        concept_evidence=[
            ConceptEvidence(
                concept_id="distributed_systems",
                score=0.4,
                evidence=["Learner struggled with consensus algorithms."],
            ),
        ],
    )

    result = agent.build_knowledge_map(payload)

    assert result.concepts
    assert 0.0 <= result.confidence <= 1.0

    counts = cast("dict[str, int]", observer.safe_summary()["counts_by_event_type"])
    assert counts.get("succeeded") == 1
    assert counts.get("fallback_used", 0) == 0
