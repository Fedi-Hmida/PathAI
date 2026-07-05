from __future__ import annotations

from app.fixtures.canonical_demo import CANONICAL_GOAL_TEXT, KNOWLEDGE_MAP
from app.fixtures.mock_agents import (
    ADAPTATION_AGENT_OUTPUT,
    ASSESSMENT_AGENT_OUTPUT,
    CRITIC_AGENT_OUTPUT,
    CURRICULUM_AGENT_OUTPUT,
    EVALUATION_AGENT_OUTPUT,
    KNOWLEDGE_MAP_AGENT_OUTPUT,
    MOCK_AGENT_GOAL_TEXT,
    MOCK_AGENT_OUTPUTS,
    QUIZ_AGENT_OUTPUT,
    QUIZ_SCORE_OUTPUT,
    RESOURCE_AGENT_OUTPUT,
)
from app.schemas.base import BaseSchema


def assert_round_trips(model: BaseSchema) -> None:
    model.__class__.model_validate(model.model_dump(mode="python"))


def test_all_mock_agent_outputs_validate() -> None:
    for output in MOCK_AGENT_OUTPUTS.values():
        assert_round_trips(output)


def test_mock_agent_outputs_cover_required_agents() -> None:
    assert set(MOCK_AGENT_OUTPUTS) == {
        "assessment",
        "assessment_score",
        "knowledge_map",
        "curriculum",
        "resource",
        "critic",
        "quiz",
        "quiz_score",
        "adaptation",
        "evaluation",
    }


def test_mock_outputs_align_with_canonical_goal_and_weak_concepts() -> None:
    assert MOCK_AGENT_GOAL_TEXT == CANONICAL_GOAL_TEXT
    assert KNOWLEDGE_MAP_AGENT_OUTPUT.weak_concepts == KNOWLEDGE_MAP.weak_concepts
    assert "retrieval_evaluation" in QUIZ_SCORE_OUTPUT.weak_concepts
    assert "retrieval_evaluation" in ADAPTATION_AGENT_OUTPUT.changes[0].affected_concept_ids


def test_mock_outputs_are_structural_contracts_only() -> None:
    assert ASSESSMENT_AGENT_OUTPUT.question.target_concepts
    assert CURRICULUM_AGENT_OUTPUT.weeks
    assert RESOURCE_AGENT_OUTPUT.coverage_summary.topics_with_resources >= 0
    assert CRITIC_AGENT_OUTPUT.overall_score >= 0.8
    assert QUIZ_AGENT_OUTPUT.questions
    assert EVALUATION_AGENT_OUTPUT.weighted_score >= 0.8
