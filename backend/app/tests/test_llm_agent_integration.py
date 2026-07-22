from __future__ import annotations

from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.llm import LLMKnowledgeMapAgent
from app.agents.mock import MockKnowledgeMapAgent
from app.agents.services import (
    AgentIntegrationSwitches,
    KnowledgeMapAgentMode,
    KnowledgeMapAgentService,
    build_mock_agent_service_bundle,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput


def test_llm_knowledge_map_agent_uses_fake_structured_output() -> None:
    payload = _knowledge_map_payload()
    client = _fake_knowledge_map_client(payload)
    agent = LLMKnowledgeMapAgent(
        client=client,
        fallback_agent=MockKnowledgeMapAgent(),
    )

    output = agent.build_knowledge_map(_knowledge_map_input())

    assert output.summary == payload.summary
    assert "retrieval_evaluation" in output.weak_concepts
    assert client.call_count == 1


def test_llm_knowledge_map_service_persists_validated_output() -> None:
    container = ApiServiceContainer()
    payload = _knowledge_map_payload()
    agent = LLMKnowledgeMapAgent(
        client=_fake_knowledge_map_client(payload),
        fallback_agent=MockKnowledgeMapAgent(),
    )
    service = KnowledgeMapAgentService(agent, container.knowledge_map_service)

    goal = container.goal_service.create(demo.LEARNING_GOAL)
    assessment = container.assessment_service.create_session(demo.ASSESSMENT_SESSION)
    for answer in demo.ASSESSMENT_ANSWERS:
        container.assessment_service.create_answer(answer)

    knowledge_map = service.build(
        goal,
        assessment,
        container.assessment_service.list_answers_by_session_id(
            assessment.assessment_session_id,
        ),
    )

    assert knowledge_map.summary == payload.summary
    assert container.knowledge_map_service.get_by_id(demo.KNOWLEDGE_MAP_ID) == (
        knowledge_map
    )


def test_agent_bundle_can_switch_knowledge_map_to_injected_llm_agent() -> None:
    container = ApiServiceContainer()
    payload = _knowledge_map_payload()
    llm_agent = LLMKnowledgeMapAgent(
        client=_fake_knowledge_map_client(payload),
        fallback_agent=MockKnowledgeMapAgent(),
    )

    agents = build_mock_agent_service_bundle(
        goals=container.goal_service,
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
        knowledge_map_agent=llm_agent,
    )

    assert agents.knowledge_map.agent is llm_agent


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )


def _knowledge_map_payload() -> KnowledgeMapAgentOutput:
    return build_knowledge_map_output(_knowledge_map_input()).model_copy(
        update={
            "summary": (
                "LLM-backed fake path validated retrieval evaluation and vector "
                "search as remediation priorities."
            ),
        },
        deep=True,
    )


def _fake_knowledge_map_client(payload: KnowledgeMapAgentOutput) -> FakeLLMClient:
    return FakeLLMClient(
        payloads={
            KnowledgeMapAgentOutput.__name__: payload.model_dump(mode="json"),
        },
    )
