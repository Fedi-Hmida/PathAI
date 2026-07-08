from __future__ import annotations

import pytest

from app.agents.deterministic.critic import build_critic_output
from app.agents.errors import AgentError
from app.agents.llm import LLMCriticAgent
from app.agents.mock import MockCriticAgent
from app.agents.services import (
    AgentIntegrationSwitches,
    CriticAgentMode,
    CriticAgentService,
    build_mock_agent_service_bundle,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient, FakeLLMScenario
from app.schemas.critic import CriticAgentInput, CriticAgentOutput


def test_agent_bundle_defaults_to_deterministic_critic_agent() -> None:
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

    assert isinstance(agents.critic.agent, MockCriticAgent)


def test_llm_critic_mode_requires_injected_agent() -> None:
    container = ApiServiceContainer()

    with pytest.raises(ValueError, match="requires an injected critic agent"):
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
                critic_agent_mode=CriticAgentMode.LLM,
            ),
        )


def test_llm_critic_agent_uses_fake_structured_output() -> None:
    payload = _critic_payload()
    client = _fake_critic_client(payload)
    agent = LLMCriticAgent(
        client=client,
        fallback_agent=MockCriticAgent(),
    )

    output = agent.review_curriculum(_critic_input())

    assert output == payload
    assert client.call_count == 1


def test_llm_critic_service_persists_validated_output() -> None:
    container = ApiServiceContainer()
    payload = _critic_payload()
    agent = LLMCriticAgent(
        client=_fake_critic_client(payload),
        fallback_agent=MockCriticAgent(),
    )
    service = CriticAgentService(agent, container.critic_service)

    review = service.review(
        demo.LEARNING_GOAL,
        demo.KNOWLEDGE_MAP,
        demo.CURRICULUM,
        demo.RESOURCE_ATTACHMENTS,
    )

    assert review == container.critic_service.get_by_id(demo.CRITIC_REVIEW_ID)
    assert review.overall_score == payload.overall_score


def test_llm_critic_agent_falls_back_on_invalid_output() -> None:
    agent = LLMCriticAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.INVALID_JSON),
        fallback_agent=MockCriticAgent(),
        fallback_on_error=True,
    )

    output = agent.review_curriculum(_critic_input())

    assert output == build_critic_output(_critic_input())


def test_llm_critic_agent_can_fail_safely_without_fallback() -> None:
    agent = LLMCriticAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON),
        fallback_agent=MockCriticAgent(),
        fallback_on_error=False,
    )

    with pytest.raises(AgentError) as error:
        agent.review_curriculum(_critic_input())

    assert error.value.agent_name == "critic_llm"
    assert "failed safely" in str(error.value)


def _critic_input() -> CriticAgentInput:
    return CriticAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resource_attachments=demo.RESOURCE_ATTACHMENTS,
        rubric_weights={},
    )


def _critic_payload() -> CriticAgentOutput:
    return build_critic_output(_critic_input())


def _fake_critic_client(payload: CriticAgentOutput) -> FakeLLMClient:
    return FakeLLMClient(
        payloads={
            CriticAgentOutput.__name__: payload.model_dump(mode="json"),
        },
    )