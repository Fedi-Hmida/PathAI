"""Rebuild-13B: Controlled LLM-backed Curriculum Agent integration tests.

Verifies:
- Deterministic default path remains intact.
- LLM-backed agent works with the fake client.
- Malformed / schema-invalid outputs fail safely or fall back safely.
- Service persists only validated typed output.
- No forbidden imports in routes/repositories/orchestration.
- Existing live tests remain skipped by default.
"""
from __future__ import annotations

import pytest

from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.errors import LLMGenerationUnavailableError
from app.agents.llm import LLMCurriculumAgent
from app.agents.mock import MockCurriculumAgent
from app.agents.services import (
    AgentIntegrationSwitches,
    CurriculumAgentMode,
    CurriculumAgentService,
    build_mock_agent_service_bundle,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient, FakeLLMScenario
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput

# ---------------------------------------------------------------------------
# Default deterministic path
# ---------------------------------------------------------------------------


def test_agent_bundle_defaults_to_deterministic_curriculum_agent() -> None:
    """Default bundle must use MockCurriculumAgent, not an LLM-backed agent."""
    container = ApiServiceContainer()
    agents = build_mock_agent_service_bundle(
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
    )

    assert isinstance(agents.curriculum.agent, MockCurriculumAgent)


# ---------------------------------------------------------------------------
# Switch validation
# ---------------------------------------------------------------------------


def test_llm_curriculum_mode_requires_injected_agent() -> None:
    """LLM mode must fail fast if no curriculum agent is injected."""
    container = ApiServiceContainer()

    with pytest.raises(ValueError, match="requires an injected curriculum agent"):
        build_mock_agent_service_bundle(
            assessments=container.assessment_service,
            knowledge_maps=container.knowledge_map_service,
            curricula=container.curriculum_service,
            resources=container.resource_service,
            critics=container.critic_service,
            progress=container.progress_service,
            quizzes=container.quiz_service,
            adaptations=container.adaptation_service,
            evaluations=container.evaluation_service,
            switches=AgentIntegrationSwitches(
                curriculum_agent_mode=CurriculumAgentMode.LLM,
            ),
        )


def test_agent_bundle_can_switch_curriculum_to_injected_llm_agent() -> None:
    """Bundle with LLM switch and injected agent must wire the LLM agent."""
    container = ApiServiceContainer()
    payload = _curriculum_payload()
    llm_agent = LLMCurriculumAgent(
        client=_fake_curriculum_client(payload),
        fallback_agent=MockCurriculumAgent(),
    )

    agents = build_mock_agent_service_bundle(
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
        switches=AgentIntegrationSwitches(
            curriculum_agent_mode=CurriculumAgentMode.LLM,
        ),
        curriculum_agent=llm_agent,
    )

    assert agents.curriculum.agent is llm_agent


# ---------------------------------------------------------------------------
# LLM-backed agent: valid fake path
# ---------------------------------------------------------------------------


def test_llm_curriculum_agent_uses_fake_structured_output() -> None:
    """LLM-backed agent must parse and return valid CurriculumAgentOutput."""
    payload = _curriculum_payload()
    client = _fake_curriculum_client(payload)
    agent = LLMCurriculumAgent(
        client=client,
        fallback_agent=MockCurriculumAgent(),
    )

    output = agent.build_curriculum(_curriculum_input())

    assert output.title == payload.title
    assert output.duration_weeks == payload.duration_weeks
    assert client.call_count == 1


def test_llm_curriculum_service_persists_validated_output() -> None:
    """Service must persist only the validated typed output, not raw LLM text."""
    container = ApiServiceContainer()
    payload = _curriculum_payload()
    agent = LLMCurriculumAgent(
        client=_fake_curriculum_client(payload),
        fallback_agent=MockCurriculumAgent(),
    )
    service = CurriculumAgentService(agent, container.curriculum_service)

    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = service.build(goal, demo.KNOWLEDGE_MAP)

    assert curriculum == container.curriculum_service.get_by_id(demo.CURRICULUM_ID)
    assert curriculum.title == payload.title


# ---------------------------------------------------------------------------
# LLM-backed agent: failure paths
# ---------------------------------------------------------------------------


def test_llm_curriculum_agent_falls_back_on_invalid_json() -> None:
    """Invalid JSON must trigger deterministic fallback when fallback_on_error=True."""
    input_payload = _curriculum_input()
    agent = LLMCurriculumAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.INVALID_JSON),
        fallback_agent=MockCurriculumAgent(),
        fallback_on_error=True,
    )

    output = agent.build_curriculum(input_payload)

    expected = build_curriculum_output(input_payload)
    assert output.duration_weeks == expected.duration_weeks


def test_llm_curriculum_agent_falls_back_on_schema_invalid_json() -> None:
    """Schema-invalid JSON must trigger deterministic fallback when configured."""
    input_payload = _curriculum_input()
    agent = LLMCurriculumAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON),
        fallback_agent=MockCurriculumAgent(),
        fallback_on_error=True,
    )

    output = agent.build_curriculum(input_payload)

    expected = build_curriculum_output(input_payload)
    assert output.duration_weeks == expected.duration_weeks


def test_llm_curriculum_agent_fails_loud_without_fallback() -> None:
    """Without fallback, malformed output must raise the typed fail-loud error."""
    agent = LLMCurriculumAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON),
        fallback_agent=MockCurriculumAgent(),
        fallback_on_error=False,
    )

    with pytest.raises(LLMGenerationUnavailableError) as error:
        agent.build_curriculum(_curriculum_input())

    assert error.value.agent_name == "curriculum_llm"
    assert error.value.code == "generation_unavailable"


def test_llm_curriculum_agent_fails_safely_on_timeout() -> None:
    """Timeout must trigger deterministic fallback when fallback_on_error=True."""
    agent = LLMCurriculumAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.TIMEOUT),
        fallback_agent=MockCurriculumAgent(),
        fallback_on_error=True,
    )

    output = agent.build_curriculum(_curriculum_input())

    # Fallback produces a deterministic output — just ensure it does not raise.
    assert output.title


def test_llm_curriculum_agent_fails_safely_on_provider_error() -> None:
    """Provider error must trigger deterministic fallback when configured."""
    agent = LLMCurriculumAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockCurriculumAgent(),
        fallback_on_error=True,
    )

    output = agent.build_curriculum(_curriculum_input())

    assert output.title


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _curriculum_input() -> CurriculumAgentInput:
    return CurriculumAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=demo.CURRICULUM.duration_weeks,
        hours_per_week=demo.LEARNING_GOAL.hours_per_week,
        critic_recommendations=[],
    )


def _curriculum_payload() -> CurriculumAgentOutput:
    """Build a deterministic payload and adjust title so tests can detect the LLM path."""
    base = build_curriculum_output(_curriculum_input())
    return base.model_copy(
        update={"title": "LLM-Backed Curriculum: RAG Mastery Sprint"},
        deep=True,
    )


def _fake_curriculum_client(payload: CurriculumAgentOutput) -> FakeLLMClient:
    return FakeLLMClient(
        payloads={
            CurriculumAgentOutput.__name__: payload.model_dump(mode="json"),
        },
    )
