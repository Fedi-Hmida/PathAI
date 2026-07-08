from __future__ import annotations

from app.agents.mock import (
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockKnowledgeMapAgent,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.nodes import OrchestrationContext


def test_default_orchestration_context_uses_mock_knowledge_map_agent() -> None:
    container = ApiServiceContainer()

    context = OrchestrationContext.from_container(container)

    assert isinstance(context.agent_services.knowledge_map.agent, MockKnowledgeMapAgent)


def test_default_orchestration_context_uses_mock_agents_for_all_switchable_roles() -> None:
    container = ApiServiceContainer()

    context = OrchestrationContext.from_container(container)

    bundle = context.agent_services
    assert isinstance(bundle.assessment.agent, MockAssessorAgent)
    assert isinstance(bundle.knowledge_map.agent, MockKnowledgeMapAgent)
    assert isinstance(bundle.critic.agent, MockCriticAgent)
    assert isinstance(bundle.curriculum.agent, MockCurriculumAgent)
