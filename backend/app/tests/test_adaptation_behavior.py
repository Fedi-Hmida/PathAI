from __future__ import annotations

from app.agents.mock import MockAdapterAgent, MockQuizAgent
from app.agents.services.adaptation import AdaptationAgentService
from app.agents.services.quiz import QuizAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.repositories.errors import DuplicateRecordError
from app.schemas.adaptation import AdaptationAgentInput, AdaptationAgentOutput
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import AdaptationStatus, AdaptationTriggerType, CurriculumChangeType
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAttemptDTO


def test_adaptation_agent_suggests_remediation_from_low_score() -> None:
    progress, attempt = _progress_and_attempt()
    output = MockAdapterAgent().plan_adaptation(
        AdaptationAgentInput(
            goal_text=demo.CANONICAL_GOAL_TEXT,
            curriculum=demo.CURRICULUM,
            progress_state=progress,
            quiz_attempt=attempt,
            weak_concepts=progress.weak_concepts,
            stuck_events=progress.stuck_events,
        ),
    )

    assert AdaptationAgentOutput.model_validate(output) == output
    assert "threshold" in output.trigger_reason
    assert output.changes
    assert output.changes[0].change_type in {
        CurriculumChangeType.ADD_PRACTICE_EXERCISE,
        CurriculumChangeType.ADD_REVIEW_QUIZ,
        CurriculumChangeType.ADD_RESOURCE,
    }
    assert output.added_practice_topics
    assert "changing the active curriculum" in output.expected_benefit


def test_adaptation_service_persists_proposed_event_without_curriculum_mutation() -> None:
    container = ApiServiceContainer()
    service = AdaptationAgentService(MockAdapterAgent(), container.adaptation_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress, attempt = _progress_and_attempt(container)

    event = service.plan(goal, curriculum, progress, attempt)

    stored = container.adaptation_service.get_by_id(event.adaptation_event_id)
    assert stored == event
    assert event.status == AdaptationStatus.PROPOSED
    assert event.new_curriculum_id is None
    assert event.trigger_type == AdaptationTriggerType.QUIZ_SCORE_BELOW_THRESHOLD
    assert event.trigger_details["quiz_score"] == f"{attempt.total_score:.2f}"
    assert event.quiz_attempt_id == attempt.quiz_attempt_id


def _progress_and_attempt(
    container: ApiServiceContainer | None = None,
) -> tuple[ProgressStateDTO, QuizAttemptDTO]:
    service_container = container or ApiServiceContainer()
    quiz_service = QuizAgentService(MockQuizAgent(), service_container.quiz_service)
    goal = _create_or_get_goal(service_container)
    curriculum = _create_or_get_curriculum(service_container)
    progress = _create_or_get_progress(service_container)
    _quiz, attempt = quiz_service.build(goal, curriculum, progress)
    updated_progress = service_container.progress_service.save(
        progress.model_copy(
            update={
                "status": demo.PROGRESS_STATE.status,
                "weak_concepts": attempt.weak_concepts,
            },
            deep=True,
        ),
    )
    return updated_progress, attempt


def _create_or_get_goal(container: ApiServiceContainer) -> LearningGoalDTO:
    try:
        return container.goal_service.create(demo.LEARNING_GOAL)
    except DuplicateRecordError:
        return container.goal_service.get_by_id(demo.GOAL_ID)


def _create_or_get_curriculum(container: ApiServiceContainer) -> CurriculumDTO:
    try:
        return container.curriculum_service.create(demo.CURRICULUM)
    except DuplicateRecordError:
        return container.curriculum_service.get_by_id(demo.CURRICULUM_ID)


def _create_or_get_progress(container: ApiServiceContainer) -> ProgressStateDTO:
    try:
        return container.progress_service.create(demo.PROGRESS_STATE)
    except DuplicateRecordError:
        return container.progress_service.get_by_id(demo.PROGRESS_ID)
