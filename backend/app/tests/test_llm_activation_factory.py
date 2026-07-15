from __future__ import annotations

import pytest

from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.llm.assessment import LLMAssessmentAgent
from app.agents.llm.client_selection import (
    UnselectableLLMProviderError,
    build_llm_client_for_agent,
)
from app.agents.llm.critic import LLMCriticAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.mock import (
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockKnowledgeMapAgent,
)
from app.agents.services.activation import build_injected_agents
from app.agents.services.bundle import (
    AgentIntegrationSwitches,
    AssessmentAgentMode,
    CriticAgentMode,
    CurriculumAgentMode,
    KnowledgeMapAgentMode,
    build_mock_agent_service_bundle,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import Settings
from app.fixtures import canonical_demo as demo
from app.llm.fake_client import FakeLLMClient
from app.llm.live_client import LiveLLMNotConfiguredError
from app.llm.observability.budget import RunScopedBudgetObserver
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput


def test_default_switches_produce_no_injected_agents() -> None:
    injected = build_injected_agents(AgentIntegrationSwitches(), Settings())

    assert injected.assessment is None
    assert injected.knowledge_map is None
    assert injected.critic is None
    assert injected.curriculum is None


def test_assessment_llm_switch_builds_fail_loud_agent_by_default() -> None:
    switches = AgentIntegrationSwitches(assessment_agent_mode=AssessmentAgentMode.LLM)
    settings = Settings(llm_provider="fake")

    injected = build_injected_agents(switches, settings)

    assert isinstance(injected.assessment, LLMAssessmentAgent)
    assert isinstance(injected.assessment.client, FakeLLMClient)
    # Fail-loud is the default (PATHAI_LLM_FALLBACK_MODE unset): no silent
    # deterministic fallback is wired in.
    assert injected.assessment.fallback_agent is None
    assert injected.assessment.fallback_on_error is False
    assert injected.knowledge_map is None
    assert injected.critic is None
    assert injected.curriculum is None


def test_knowledge_map_llm_switch_builds_fail_loud_agent_by_default() -> None:
    switches = AgentIntegrationSwitches(knowledge_map_agent_mode=KnowledgeMapAgentMode.LLM)
    settings = Settings(llm_provider="fake")

    injected = build_injected_agents(switches, settings)

    assert isinstance(injected.knowledge_map, LLMKnowledgeMapAgent)
    assert isinstance(injected.knowledge_map.client, FakeLLMClient)
    assert injected.knowledge_map.fallback_agent is None
    assert injected.knowledge_map.fallback_on_error is False
    # Rebuild-22B: every agent now shares one run-scoped observer instead of
    # its own independent LoggingObserver.
    assert isinstance(injected.knowledge_map.observer, RunScopedBudgetObserver)


def test_critic_llm_switch_builds_fail_loud_agent_by_default() -> None:
    switches = AgentIntegrationSwitches(critic_agent_mode=CriticAgentMode.LLM)
    settings = Settings(llm_provider="fake")

    injected = build_injected_agents(switches, settings)

    assert isinstance(injected.critic, LLMCriticAgent)
    assert isinstance(injected.critic.client, FakeLLMClient)
    assert injected.critic.fallback_agent is None
    assert injected.critic.fallback_on_error is False


def test_curriculum_llm_switch_builds_fail_loud_agent_by_default() -> None:
    switches = AgentIntegrationSwitches(curriculum_agent_mode=CurriculumAgentMode.LLM)
    settings = Settings(llm_provider="fake")

    injected = build_injected_agents(switches, settings)

    assert isinstance(injected.curriculum, LLMCurriculumAgent)
    assert isinstance(injected.curriculum.client, FakeLLMClient)
    assert injected.curriculum.fallback_agent is None
    assert injected.curriculum.fallback_on_error is False


def test_deterministic_fallback_mode_wires_mock_agents_behind_explicit_setting() -> None:
    # PATHAI_LLM_FALLBACK_MODE=deterministic is the explicit opt-in that keeps
    # the legacy degrade-on-failure behavior (offline tests / offline demo).
    switches = AgentIntegrationSwitches(
        assessment_agent_mode=AssessmentAgentMode.LLM,
        knowledge_map_agent_mode=KnowledgeMapAgentMode.LLM,
        critic_agent_mode=CriticAgentMode.LLM,
        curriculum_agent_mode=CurriculumAgentMode.LLM,
    )
    settings = Settings(llm_provider="fake", llm_fallback_mode="deterministic")

    injected = build_injected_agents(switches, settings)

    assert isinstance(injected.assessment, LLMAssessmentAgent)
    assert isinstance(injected.knowledge_map, LLMKnowledgeMapAgent)
    assert isinstance(injected.critic, LLMCriticAgent)
    assert isinstance(injected.curriculum, LLMCurriculumAgent)
    assert isinstance(injected.assessment.fallback_agent, MockAssessorAgent)
    assert injected.assessment.fallback_on_error is True
    assert isinstance(injected.knowledge_map.fallback_agent, MockKnowledgeMapAgent)
    assert injected.knowledge_map.fallback_on_error is True
    assert isinstance(injected.critic.fallback_agent, MockCriticAgent)
    assert injected.critic.fallback_on_error is True
    assert isinstance(injected.curriculum.fallback_agent, MockCurriculumAgent)
    assert injected.curriculum.fallback_on_error is True


def test_llm_switch_with_mock_provider_raises_unselectable_provider_error() -> None:
    switches = AgentIntegrationSwitches(knowledge_map_agent_mode=KnowledgeMapAgentMode.LLM)
    settings = Settings(llm_provider="mock")

    with pytest.raises(UnselectableLLMProviderError):
        build_injected_agents(switches, settings)


def test_llm_switch_with_incomplete_live_provider_propagates_not_configured_error() -> None:
    settings = Settings(llm_provider="openai_compatible")

    with pytest.raises(LiveLLMNotConfiguredError):
        build_llm_client_for_agent(settings)


def test_end_to_end_fake_provider_bundle_produces_valid_knowledge_map_output() -> None:
    container = ApiServiceContainer()
    switches = AgentIntegrationSwitches(knowledge_map_agent_mode=KnowledgeMapAgentMode.LLM)
    settings = Settings(llm_provider="fake")
    injected = build_injected_agents(switches, settings)
    assert isinstance(injected.knowledge_map, LLMKnowledgeMapAgent)
    fake_client = injected.knowledge_map.client
    assert isinstance(fake_client, FakeLLMClient)
    fake_client.payloads[KnowledgeMapAgentOutput.__name__] = _fake_knowledge_map_payload()

    bundle = build_mock_agent_service_bundle(
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
        switches=switches,
        knowledge_map_agent=injected.knowledge_map,
    )

    assert bundle.knowledge_map.agent is injected.knowledge_map

    output = bundle.knowledge_map.agent.build_knowledge_map(_knowledge_map_input())

    assert isinstance(output, KnowledgeMapAgentOutput)
    assert fake_client.call_count == 1


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )


def _fake_knowledge_map_payload() -> dict[str, object]:
    deterministic_output = build_knowledge_map_output(_knowledge_map_input())
    return deterministic_output.model_dump(mode="json")
