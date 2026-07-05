from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.fixtures.canonical_demo import CANONICAL_GOAL_TEXT, CURRICULUM, LEARNER_PROFILE
from app.schemas.goal import LearningGoalCreate, LearningGoalSummary
from app.schemas.knowledge_map import ConceptMasteryDTO


def test_learning_goal_create_accepts_valid_payload() -> None:
    goal = LearningGoalCreate(
        goal_text=CANONICAL_GOAL_TEXT,
        learner_profile=LEARNER_PROFILE,
        demo_mode=True,
    )

    assert goal.goal_text == CANONICAL_GOAL_TEXT
    assert goal.learner_profile == LEARNER_PROFILE


def test_invalid_status_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        LearningGoalSummary.model_validate(
            {
                "goal_id": "goal_demo_rag",
                "text": CANONICAL_GOAL_TEXT,
                "status": "not_a_real_status",
            }
        )


def test_invalid_score_range_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ConceptMasteryDTO(
            concept_id="retrieval_evaluation",
            label="Retrieval evaluation",
            mastery_score=1.5,
            classification="weak",
        )


def test_invalid_id_prefix_is_rejected() -> None:
    with pytest.raises(ValidationError):
        LearningGoalSummary(
            goal_id="bad_demo_rag",
            text=CANONICAL_GOAL_TEXT,
            status="active",
        )


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        LearningGoalCreate.model_validate(
            {
                "goal_text": CANONICAL_GOAL_TEXT,
                "demo_mode": True,
                "unexpected": "not allowed",
            }
        )


def test_curriculum_duration_must_match_week_count() -> None:
    payload = CURRICULUM.model_dump(mode="python")
    payload["duration_weeks"] = 5

    with pytest.raises(ValidationError):
        CURRICULUM.__class__.model_validate(payload)
