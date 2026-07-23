from __future__ import annotations

import re

from app.agents.mock import MockAdapterAgent, MockQuizAgent
from app.agents.services.adaptation import AdaptationAgentService
from app.agents.services.quiz import QuizAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.repositories.errors import DuplicateRecordError
from app.schemas.adaptation import AdaptationAgentInput, AdaptationAgentOutput
from app.schemas.curriculum import (
    CurriculumDTO,
    CurriculumTopicDTO,
    CurriculumWeekDTO,
)
from app.schemas.enums import (
    AdaptationStatus,
    AdaptationTriggerType,
    CurriculumChangeType,
    CurriculumStatus,
    DifficultyLevel,
    GoalStatus,
    ProgressStatus,
    QuizAttemptStatus,
    TopicProgressStatus,
)
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.progress import ProgressStateDTO, StuckEventDTO, TopicProgressDTO
from app.schemas.quiz import ConceptQuizScore, QuizAnswerSubmission, QuizAttemptDTO

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def _assert_no_rag_vocabulary(*fragments: str) -> None:
    blob = " ".join(fragments)
    match = _RAG_TOKEN_PATTERN.search(blob)
    assert match is None, f"RAG vocabulary leaked into non-RAG adaptation output: {match!r}"


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


def test_practice_topics_carry_the_real_event_id_not_the_fixed_demo_one() -> None:
    """ADR-0003's most severe finding: every generated practice topic used to
    be unconditionally stamped with the fixed demo adaptation ID regardless
    of which real event produced it. Confirm the real ID, once threaded
    through the payload, is what actually gets stamped."""
    progress, attempt = _progress_and_attempt()
    output = MockAdapterAgent().plan_adaptation(
        AdaptationAgentInput(
            goal_text=demo.CANONICAL_GOAL_TEXT,
            curriculum=demo.CURRICULUM,
            progress_state=progress,
            quiz_attempt=attempt,
            weak_concepts=progress.weak_concepts,
            stuck_events=progress.stuck_events,
            adaptation_event_id="adapt_real_event_for_this_test",
        ),
    )

    assert output.added_practice_topics
    for topic in output.added_practice_topics:
        assert topic.adaptation_origin == "adapt_real_event_for_this_test"
        assert topic.adaptation_origin != demo.ADAPTATION_ID


def test_weak_concepts_never_falls_back_to_rag_vocabulary() -> None:
    """ADR-0003: `_weak_concepts` used to fall back to a hardcoded
    ["retrieval_evaluation"] whenever no real weak concept was found from any
    source. With no payload/quiz-attempt/progress weak concepts but a real
    stuck event carrying its own concept_ids, the real stuck-event concept
    must be used instead - never the RAG fixture term."""
    curriculum = _non_rag_curriculum(
        curriculum_id="curriculum_stuck_only",
        goal_id="goal_stuck_only",
    )
    progress = ProgressStateDTO(
        progress_state_id="progress_stuck_only",
        goal_id="goal_stuck_only",
        curriculum_id="curriculum_stuck_only",
        status=ProgressStatus.ADAPTATION_NEEDED,
        overall_completion=0.2,
        current_topic_id="topic_chords",
        topic_progress=[
            TopicProgressDTO(
                topic_id="topic_chords",
                status=TopicProgressStatus.STUCK,
                completion=0.2,
                stuck_count=2,
            ),
        ],
        weak_concepts=[],
        stuck_events=[
            StuckEventDTO(
                topic_id="topic_chords",
                concept_ids=["chord_progressions"],
                reason="Deterministic quiz evidence crossed the stuck-topic threshold.",
                created_at=demo.NOW,
            ),
        ],
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )

    output = MockAdapterAgent().plan_adaptation(
        AdaptationAgentInput(
            goal_text="Learn classical guitar for a wedding performance",
            curriculum=curriculum,
            progress_state=progress,
            quiz_attempt=None,
            weak_concepts=[],
            stuck_events=progress.stuck_events,
            adaptation_event_id="adapt_stuck_only_test",
        ),
    )

    assert "chord progressions" in output.after_summary
    assert "retrieval evaluation" not in output.after_summary
    _assert_no_rag_vocabulary(
        output.trigger_reason,
        output.before_summary,
        output.after_summary,
        output.expected_benefit,
    )


def test_two_different_goals_each_get_their_own_distinct_adaptation_event() -> None:
    """ADR-0003's ID-collision defect, now as a passing test: without an
    explicit per-goal ID, learner B's plan() would hit DuplicateRecordError
    on learner A's fixed-ID record and create_or_get would silently return
    A's data."""
    container = ApiServiceContainer()
    service = AdaptationAgentService(MockAdapterAgent(), container.adaptation_service)
    goal_alice = container.goal_service.create(_non_rag_goal(goal_id="goal_alice_adapt"))
    curriculum_alice = container.curriculum_service.create(
        _non_rag_curriculum(curriculum_id="curriculum_alice_adapt", goal_id="goal_alice_adapt"),
    )
    progress_alice = _low_score_progress(
        goal_id="goal_alice_adapt",
        curriculum_id="curriculum_alice_adapt",
    )
    attempt_alice = _low_score_attempt(
        goal_id="goal_alice_adapt",
        curriculum_id="curriculum_alice_adapt",
    )

    goal_bob = container.goal_service.create(_non_rag_goal(goal_id="goal_bob_adapt"))
    curriculum_bob = container.curriculum_service.create(
        _non_rag_curriculum(curriculum_id="curriculum_bob_adapt", goal_id="goal_bob_adapt"),
    )
    progress_bob = _low_score_progress(
        goal_id="goal_bob_adapt",
        curriculum_id="curriculum_bob_adapt",
    )
    attempt_bob = _low_score_attempt(
        goal_id="goal_bob_adapt",
        curriculum_id="curriculum_bob_adapt",
    )

    event_alice = service.plan(
        goal_alice,
        curriculum_alice,
        progress_alice,
        attempt_alice,
        adaptation_event_id="adapt_alice",
    )
    event_bob = service.plan(
        goal_bob,
        curriculum_bob,
        progress_bob,
        attempt_bob,
        adaptation_event_id="adapt_bob",
    )

    assert event_alice.adaptation_event_id == "adapt_alice"
    assert event_bob.adaptation_event_id == "adapt_bob"
    assert event_alice.goal_id == "goal_alice_adapt"
    assert event_bob.goal_id == "goal_bob_adapt"
    stored_alice = container.adaptation_service.get_by_id("adapt_alice")
    stored_bob = container.adaptation_service.get_by_id("adapt_bob")
    assert stored_alice.goal_id == "goal_alice_adapt"
    assert stored_bob.goal_id == "goal_bob_adapt"


def test_retriggering_updates_the_existing_adaptation_event_in_place() -> None:
    container = ApiServiceContainer()
    service = AdaptationAgentService(MockAdapterAgent(), container.adaptation_service)
    goal = container.goal_service.create(_non_rag_goal(goal_id="goal_retrigger"))
    curriculum = container.curriculum_service.create(
        _non_rag_curriculum(curriculum_id="curriculum_retrigger", goal_id="goal_retrigger"),
    )
    progress = _low_score_progress(goal_id="goal_retrigger", curriculum_id="curriculum_retrigger")

    first_attempt = _low_score_attempt(
        goal_id="goal_retrigger",
        curriculum_id="curriculum_retrigger",
        score=0.2,
    )
    first = service.plan(
        goal,
        curriculum,
        progress,
        first_attempt,
        adaptation_event_id="adapt_retrigger",
    )

    second_attempt = _low_score_attempt(
        goal_id="goal_retrigger",
        curriculum_id="curriculum_retrigger",
        score=0.0,
    )
    second = service.plan(
        goal,
        curriculum,
        progress,
        second_attempt,
        adaptation_event_id="adapt_retrigger",
    )

    assert second.adaptation_event_id == first.adaptation_event_id
    assert second.trigger_details["quiz_score"] == "0.00"
    stored_records = container.adaptation_service.list_by_goal_id("goal_retrigger")
    assert len(stored_records) == 1
    assert stored_records[0] == second


def test_adaptation_event_for_a_non_rag_goal_contains_no_rag_content() -> None:
    goal = _non_rag_goal(goal_id="goal_leak_guard_adapt")
    curriculum = _non_rag_curriculum(
        curriculum_id="curriculum_leak_guard_adapt",
        goal_id="goal_leak_guard_adapt",
    )
    progress = _low_score_progress(
        goal_id="goal_leak_guard_adapt",
        curriculum_id="curriculum_leak_guard_adapt",
    )
    attempt = _low_score_attempt(
        goal_id="goal_leak_guard_adapt",
        curriculum_id="curriculum_leak_guard_adapt",
    )
    service = AdaptationAgentService(MockAdapterAgent(), ApiServiceContainer().adaptation_service)

    event = service.plan(
        goal,
        curriculum,
        progress,
        attempt,
        adaptation_event_id="adapt_leak_guard",
    )

    blob = event.model_dump_json().lower()
    _assert_no_rag_vocabulary(blob)
    assert "chord" in blob
    assert "adapt_leak_guard" == event.adaptation_event_id


def _non_rag_goal(*, goal_id: str) -> LearningGoalDTO:
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


def _non_rag_curriculum(*, curriculum_id: str, goal_id: str) -> CurriculumDTO:
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
                week_id="week_chords",
                week_number=1,
                theme="Chord foundations",
                estimated_hours=5.0,
                learning_outcomes=["Play basic chord progressions cleanly."],
                topics=[
                    CurriculumTopicDTO(
                        topic_id="topic_chords",
                        title="Chord progressions",
                        description="Practice common chord progressions.",
                        concept_ids=["chord_progressions"],
                        difficulty=DifficultyLevel.BEGINNER,
                        estimated_hours=5.0,
                        learning_outcomes=["Play basic chord progressions cleanly."],
                        sequence_order=1,
                    ),
                ],
            ),
        ],
    )


def _low_score_progress(*, goal_id: str, curriculum_id: str) -> ProgressStateDTO:
    return ProgressStateDTO(
        progress_state_id=f"progress_{goal_id}",
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        status=ProgressStatus.ADAPTATION_NEEDED,
        overall_completion=0.2,
        current_topic_id="topic_chords",
        topic_progress=[
            TopicProgressDTO(
                topic_id="topic_chords",
                status=TopicProgressStatus.STUCK,
                completion=0.2,
                stuck_count=2,
            ),
        ],
        weak_concepts=["chord_progressions"],
        stuck_events=[
            StuckEventDTO(
                topic_id="topic_chords",
                concept_ids=["chord_progressions"],
                reason="Deterministic quiz evidence crossed the stuck-topic threshold.",
                created_at=demo.NOW,
            ),
        ],
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _low_score_attempt(
    *,
    goal_id: str,
    curriculum_id: str,
    score: float = 0.1,
) -> QuizAttemptDTO:
    return QuizAttemptDTO(
        quiz_attempt_id=f"attempt_{goal_id}",
        quiz_id=f"quiz_{goal_id}",
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        answers=[QuizAnswerSubmission(question_id="question_001", selected_options=["A"])],
        total_score=score,
        correct_count=0,
        total_questions=1,
        concept_scores=[
            ConceptQuizScore(
                concept_id="chord_progressions",
                score=score,
                correct_count=0,
                total_questions=1,
            ),
        ],
        weak_concepts=["chord_progressions"],
        submitted_at=demo.NOW,
        status=QuizAttemptStatus.SCORED,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


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
