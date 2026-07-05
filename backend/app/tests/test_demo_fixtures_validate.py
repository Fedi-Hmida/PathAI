from __future__ import annotations

from app.fixtures.canonical_demo import (
    ADAPTATION_EVENT,
    ASSESSMENT_ANSWERS,
    ASSESSMENT_ID,
    ASSESSMENT_QUESTIONS,
    ASSESSMENT_SESSION,
    CRITIC_REVIEW,
    CURRICULUM,
    DASHBOARD_PAYLOAD,
    EVALUATION_REPORT,
    GOAL_ID,
    KNOWLEDGE_MAP,
    LEARNING_GOAL,
    PROGRESS_STATE,
    QUIZ,
    QUIZ_ATTEMPT,
    RESOURCE_ATTACHMENTS,
    RESOURCE_CORPUS,
)
from app.schemas.base import BaseSchema


def assert_round_trips(model: BaseSchema) -> None:
    model.__class__.model_validate(model.model_dump(mode="python"))


def test_canonical_demo_top_level_fixtures_validate() -> None:
    for model in [
        LEARNING_GOAL,
        ASSESSMENT_SESSION,
        KNOWLEDGE_MAP,
        CURRICULUM,
        PROGRESS_STATE,
        QUIZ,
        QUIZ_ATTEMPT,
        ADAPTATION_EVENT,
        CRITIC_REVIEW,
        EVALUATION_REPORT,
        DASHBOARD_PAYLOAD,
    ]:
        assert_round_trips(model)


def test_canonical_demo_nested_fixture_collections_validate() -> None:
    for model in [
        *ASSESSMENT_QUESTIONS,
        *ASSESSMENT_ANSWERS,
        *RESOURCE_CORPUS,
        *RESOURCE_ATTACHMENTS,
    ]:
        assert_round_trips(model)


def test_canonical_demo_fixture_ids_link_consistently() -> None:
    assert LEARNING_GOAL.goal_id == GOAL_ID
    assert ASSESSMENT_SESSION.goal_id == GOAL_ID
    assert ASSESSMENT_SESSION.assessment_session_id == ASSESSMENT_ID
    assert KNOWLEDGE_MAP.assessment_session_id == ASSESSMENT_ID
    assert CURRICULUM.knowledge_map_id == KNOWLEDGE_MAP.knowledge_map_id
    assert QUIZ.curriculum_id == CURRICULUM.curriculum_id
    assert QUIZ_ATTEMPT.quiz_id == QUIZ.quiz_id
    assert ADAPTATION_EVENT.quiz_attempt_id == QUIZ_ATTEMPT.quiz_attempt_id
    assert CRITIC_REVIEW.curriculum_id == CURRICULUM.curriculum_id
    assert EVALUATION_REPORT.goal_id == GOAL_ID


def test_resource_attachments_reference_known_resources_and_topics() -> None:
    resource_ids = {resource.resource_id for resource in RESOURCE_CORPUS}
    topic_ids = {
        topic.topic_id
        for week in CURRICULUM.weeks
        for topic in week.topics
    }

    for attachment in RESOURCE_ATTACHMENTS:
        assert attachment.resource_id in resource_ids
        assert attachment.topic_id in topic_ids


def test_dashboard_payload_matches_major_artifact_ids() -> None:
    assert DASHBOARD_PAYLOAD.goal_summary.goal_id == LEARNING_GOAL.goal_id
    assert DASHBOARD_PAYLOAD.run_summary.run_id == LEARNING_GOAL.run_id
    assert DASHBOARD_PAYLOAD.curriculum_summary is not None
    assert DASHBOARD_PAYLOAD.curriculum_summary.active_curriculum_id == CURRICULUM.curriculum_id
