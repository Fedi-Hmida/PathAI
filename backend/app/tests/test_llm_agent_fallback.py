from __future__ import annotations

import pytest

from app.agents.errors import LLMGenerationUnavailableError
from app.agents.llm import LLMKnowledgeMapAgent
from app.agents.mock import MockKnowledgeMapAgent
from app.agents.services import (
    AgentIntegrationSwitches,
    KnowledgeMapAgentMode,
    build_mock_agent_service_bundle,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient, FakeLLMScenario
from app.schemas.knowledge_map import KnowledgeMapAgentInput


def test_agent_bundle_defaults_to_deterministic_knowledge_map_agent() -> None:
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

    assert isinstance(agents.knowledge_map.agent, MockKnowledgeMapAgent)


def test_llm_knowledge_map_mode_requires_injected_agent() -> None:
    container = ApiServiceContainer()

    with pytest.raises(ValueError, match="requires an injected knowledge-map agent"):
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
                knowledge_map_agent_mode=KnowledgeMapAgentMode.LLM,
            ),
        )


def test_llm_knowledge_map_agent_falls_back_on_invalid_output() -> None:
    agent = LLMKnowledgeMapAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.INVALID_JSON),
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
    )

    output = agent.build_knowledge_map(_knowledge_map_input())

    assert "retrieval_evaluation" in output.weak_concepts
    assert output.summary.startswith("Recommended level: intermediate.")


def test_llm_knowledge_map_agent_fails_loud_without_fallback() -> None:
    agent = LLMKnowledgeMapAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.SCHEMA_INVALID_JSON),
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=False,
    )

    with pytest.raises(LLMGenerationUnavailableError) as error:
        agent.build_knowledge_map(_knowledge_map_input())

    assert error.value.agent_name == "knowledge_map_llm"
    assert error.value.code == "generation_unavailable"


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )
