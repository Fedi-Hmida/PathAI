from __future__ import annotations

import re

from app.agents.mock import MockAdapterAgent, MockProgressAgent, MockQuizAgent
from app.agents.services.adaptation import AdaptationAgentService
from app.agents.services.progress import ProgressAgentService
from app.agents.services.quiz import QuizAgentService
from app.agents.services.quiz_submission import QuizSubmissionService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO, CurriculumWeekDTO
from app.schemas.enums import AdaptationTriggerType, CurriculumStatus, DifficultyLevel, GoalStatus
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.progress import ProgressStateDTO, ProgressStatus, TopicProgressDTO
from app.schemas.progress import TopicProgressStatus as _TopicProgressStatus
from app.schemas.quiz import QuizAnswerSubmission, QuizDTO

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def _assert_no_rag_vocabulary(*fragments: str) -> None:
    blob = " ".join(fragments)
    match = _RAG_TOKEN_PATTERN.search(blob)
    assert match is None, f"RAG vocabulary leaked into non-RAG adaptation output: {match!r}"


def _submission_service(container: ApiServiceContainer) -> QuizSubmissionService:
    return QuizSubmissionService(
        quiz_agent=QuizAgentService(MockQuizAgent(), container.quiz_service),
        progress_agent=ProgressAgentService(MockProgressAgent(), container.progress_service),
        adaptation_agent=AdaptationAgentService(MockAdapterAgent(), container.adaptation_service),
        goals=container.goal_service,
        curricula=container.curriculum_service,
    )


def _goal(*, goal_id: str) -> LearningGoalDTO:
    return LearningGoalDTO(
        goal_id=goal_id,
        run_id=f"run_{goal_id}",
        goal_text="Learn classical guitar for a wedding performance",
        normalized_goal_text="learn classical guitar for a wedding performance",
        status=GoalStatus.CURRICULUM_GENERATED,
        learner_profile=LearnerProfile(
            learner_type="adult_hobbyist",
            time_availability_hours_per_week=5,
            desired_outcome="Perform a short classical guitar set at a wedding.",
            difficulty_target=DifficultyLevel.INTERMEDIATE,
        ),
        hours_per_week=5,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _curriculum(*, curriculum_id: str, goal_id: str) -> CurriculumDTO:
    # Two topics (not one) so the generated quiz question has more than one
    # option, letting a test submit a genuinely wrong answer.
    return CurriculumDTO(
        curriculum_id=curriculum_id,
        goal_id=goal_id,
        knowledge_map_id=f"kmap_{goal_id}",
        run_id=f"run_{goal_id}",
        status=CurriculumStatus.ACTIVE,
        title="Classical Guitar for a Wedding Performance",
        duration_weeks=1,
        target_outcomes=["Perform a short classical guitar set at a wedding."],
        created_at=demo.NOW,
        updated_at=demo.NOW,
        weeks=[
            CurriculumWeekDTO(
                week_id="week_guitar",
                week_number=1,
                theme="Chord and fingerpicking foundations",
                estimated_hours=5.0,
                learning_outcomes=["Play basic chord progressions cleanly."],
                topics=[
                    CurriculumTopicDTO(
                        topic_id="topic_chords",
                        title="Chord progressions",
                        description="Practice common chord progressions.",
                        concept_ids=["chord_progressions"],
                        difficulty=DifficultyLevel.BEGINNER,
                        estimated_hours=2.5,
                        learning_outcomes=["Play basic chord progressions cleanly."],
                        sequence_order=1,
                    ),
                    CurriculumTopicDTO(
                        topic_id="topic_fingerpicking",
                        title="Fingerpicking technique",
                        description="Practice fingerpicking patterns.",
                        concept_ids=["fingerpicking_technique"],
                        difficulty=DifficultyLevel.BEGINNER,
                        estimated_hours=2.5,
                        learning_outcomes=["Play a simple fingerpicking pattern."],
                        sequence_order=2,
                    ),
                ],
            ),
        ],
    )


def _progress_seed(*, goal_id: str, curriculum_id: str) -> ProgressStateDTO:
    return ProgressStateDTO(
        progress_state_id=f"progress_seed_{goal_id}",
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        status=ProgressStatus.NOT_STARTED,
        overall_completion=0.0,
        topic_progress=[
            TopicProgressDTO(
                topic_id="topic_chords",
                status=_TopicProgressStatus.NOT_STARTED,
                completion=0.0,
            ),
        ],
        weak_concepts=[],
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _build_quiz(
    container: ApiServiceContainer,
    *,
    goal_id: str,
    curriculum_id: str,
) -> tuple[LearningGoalDTO, CurriculumDTO, QuizDTO]:
    goal = container.goal_service.create(_goal(goal_id=goal_id))
    curriculum = container.curriculum_service.create(
        _curriculum(curriculum_id=curriculum_id, goal_id=goal_id),
    )
    quiz_agent = QuizAgentService(MockQuizAgent(), container.quiz_service)
    quiz = quiz_agent.build_quiz(
        goal,
        curriculum,
        _progress_seed(goal_id=goal_id, curriculum_id=curriculum_id),
        quiz_id=f"quiz_{goal_id}",
    )
    return goal, curriculum, quiz


def _answers_selecting(quiz: QuizDTO, *, correct: bool) -> list[QuizAnswerSubmission]:
    answers = []
    for question in quiz.questions:
        if correct:
            selected = question.correct_answer
        else:
            wrong_options = [
                option for option in question.options if option != question.correct_answer
            ]
            selected = wrong_options[0] if wrong_options else question.correct_answer
        answers.append(
            QuizAnswerSubmission(question_id=question.question_id, selected_options=[selected]),
        )
    return answers


def test_healthy_quiz_submission_triggers_no_adaptation_event() -> None:
    """The single most important test in this step: a healthy submission
    (good score, no stuck topics) must create zero adaptation events - the
    real fix for `_trigger_type()`'s always-true final fallback."""
    container = ApiServiceContainer()
    goal, _curric, quiz = _build_quiz(
        container,
        goal_id="goal_healthy_submit",
        curriculum_id="curriculum_healthy_submit",
    )
    service = _submission_service(container)

    result = service.submit(quiz, _answers_selecting(quiz, correct=True))

    assert result.attempt.total_score >= 0.65
    assert result.adaptation_event is None
    assert container.adaptation_service.list_by_goal_id(goal.goal_id) == []


def test_low_score_quiz_submission_triggers_a_real_adaptation_event() -> None:
    container = ApiServiceContainer()
    goal, _curric, quiz = _build_quiz(
        container,
        goal_id="goal_low_score_submit",
        curriculum_id="curriculum_low_score_submit",
    )
    service = _submission_service(container)

    result = service.submit(quiz, _answers_selecting(quiz, correct=False))

    assert result.attempt.total_score < 0.65
    assert result.adaptation_event is not None
    assert (
        result.adaptation_event.trigger_type == AdaptationTriggerType.QUIZ_SCORE_BELOW_THRESHOLD
    )
    assert (
        result.adaptation_event.trigger_details["quiz_score"]
        == f"{result.attempt.total_score:.2f}"
    )
    assert result.adaptation_event.goal_id == goal.goal_id
    stored = container.adaptation_service.get_by_id(result.adaptation_event.adaptation_event_id)
    assert stored == result.adaptation_event


def test_two_goals_each_get_their_own_distinct_adaptation_event_via_submission() -> None:
    container = ApiServiceContainer()
    goal_a, _ca, quiz_a = _build_quiz(
        container,
        goal_id="goal_submit_alice",
        curriculum_id="curriculum_submit_alice",
    )
    goal_b, _cb, quiz_b = _build_quiz(
        container,
        goal_id="goal_submit_bob",
        curriculum_id="curriculum_submit_bob",
    )
    service = _submission_service(container)

    result_a = service.submit(quiz_a, _answers_selecting(quiz_a, correct=False))
    result_b = service.submit(quiz_b, _answers_selecting(quiz_b, correct=False))

    assert result_a.adaptation_event is not None
    assert result_b.adaptation_event is not None
    assert (
        result_a.adaptation_event.adaptation_event_id
        != result_b.adaptation_event.adaptation_event_id
    )
    assert result_a.adaptation_event.goal_id == goal_a.goal_id
    assert result_b.adaptation_event.goal_id == goal_b.goal_id


def test_second_low_score_submission_updates_the_existing_adaptation_event_in_place() -> None:
    container = ApiServiceContainer()
    goal, _curric, quiz = _build_quiz(
        container,
        goal_id="goal_submit_retrigger",
        curriculum_id="curriculum_submit_retrigger",
    )
    service = _submission_service(container)

    first = service.submit(quiz, _answers_selecting(quiz, correct=False))
    second = service.submit(quiz, _answers_selecting(quiz, correct=False))

    assert first.adaptation_event is not None
    assert second.adaptation_event is not None
    assert (
        first.adaptation_event.adaptation_event_id == second.adaptation_event.adaptation_event_id
    )
    stored_events = container.adaptation_service.list_by_goal_id(goal.goal_id)
    assert len(stored_events) == 1
    assert stored_events[0] == second.adaptation_event
    # Progress must also update the same record in place, not duplicate it.
    stored_progress = container.progress_service.list_by_goal_id(goal.goal_id)
    assert len(stored_progress) == 1


def test_submission_triggered_adaptation_event_for_a_non_rag_goal_has_no_rag_content() -> None:
    container = ApiServiceContainer()
    _goal_obj, _curric, quiz = _build_quiz(
        container,
        goal_id="goal_submit_leak_guard",
        curriculum_id="curriculum_submit_leak_guard",
    )
    service = _submission_service(container)

    result = service.submit(quiz, _answers_selecting(quiz, correct=False))

    assert result.adaptation_event is not None
    blob = result.adaptation_event.model_dump_json().lower()
    _assert_no_rag_vocabulary(blob)
    assert "chord" in blob or "fingerpicking" in blob
