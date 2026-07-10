from __future__ import annotations

from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.mock import MockCriticAgent, MockCurriculumAgent
from app.agents.services.critic import CriticAgentService
from app.agents.services.curriculum import CurriculumAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput


class _CapturingCurriculumAgent:
    """Deterministic curriculum agent that records every input it receives."""

    agent_name = "curriculum"

    def __init__(self) -> None:
        self.seen: list[CurriculumAgentInput] = []

    def build_curriculum(self, payload: CurriculumAgentInput) -> CurriculumAgentOutput:
        self.seen.append(payload)
        return build_curriculum_output(payload)


def test_curriculum_first_pass_is_unchanged_create_or_get() -> None:
    container = ApiServiceContainer()
    service = CurriculumAgentService(
        agent=MockCurriculumAgent(),
        curricula=container.curriculum_service,
    )

    first = service.build(demo.LEARNING_GOAL, demo.KNOWLEDGE_MAP)

    assert first.critic_revision_attempt == 0
    assert first.revision_reason is None


def test_curriculum_revision_overwrites_in_place_same_id() -> None:
    container = ApiServiceContainer()
    service = CurriculumAgentService(
        agent=MockCurriculumAgent(),
        curricula=container.curriculum_service,
    )

    first = service.build(demo.LEARNING_GOAL, demo.KNOWLEDGE_MAP)
    revised = service.build(
        demo.LEARNING_GOAL,
        demo.KNOWLEDGE_MAP,
        critic_recommendations=["deepen coverage of weak concepts"],
        revision_attempt=1,
    )

    assert revised.curriculum_id == first.curriculum_id
    assert revised.critic_revision_attempt == 1
    assert revised.revision_reason is not None

    stored = container.curriculum_service.get_by_id(first.curriculum_id)
    assert stored.critic_revision_attempt == 1


def test_curriculum_recommendations_reach_the_agent_input() -> None:
    container = ApiServiceContainer()
    agent = _CapturingCurriculumAgent()
    service = CurriculumAgentService(agent=agent, curricula=container.curriculum_service)

    service.build(demo.LEARNING_GOAL, demo.KNOWLEDGE_MAP)
    assert agent.seen[-1].critic_recommendations == []

    service.build(
        demo.LEARNING_GOAL,
        demo.KNOWLEDGE_MAP,
        critic_recommendations=["add a spaced-repetition checkpoint"],
        revision_attempt=1,
    )
    assert agent.seen[-1].critic_recommendations == ["add a spaced-repetition checkpoint"]


def test_critic_review_revision_overwrites_in_place_same_id() -> None:
    container = ApiServiceContainer()
    service = CriticAgentService(agent=MockCriticAgent(), critics=container.critic_service)

    first = service.review(
        demo.LEARNING_GOAL,
        demo.KNOWLEDGE_MAP,
        demo.CURRICULUM,
        demo.RESOURCE_ATTACHMENTS,
    )
    assert first.revision_attempt == 0

    revised = service.review(
        demo.LEARNING_GOAL,
        demo.KNOWLEDGE_MAP,
        demo.CURRICULUM,
        demo.RESOURCE_ATTACHMENTS,
        revision_attempt=1,
    )

    assert revised.critic_review_id == first.critic_review_id
    assert revised.revision_attempt == 1

    stored = container.critic_service.get_by_id(first.critic_review_id)
    assert stored.revision_attempt == 1
