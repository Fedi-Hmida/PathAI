from __future__ import annotations

import re

from app.agents.mock import MockProgressAgent, MockQuizAgent
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.quiz import QuizAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO, CurriculumWeekDTO
from app.schemas.enums import (
    CurriculumStatus,
    DifficultyLevel,
    GoalStatus,
    ProgressStatus,
    TopicProgressStatus,
)
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.quiz import ConceptQuizScore, QuizAnswerSubmission, QuizAttemptDTO, QuizDTO

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def _assert_no_rag_vocabulary(*fragments: str) -> None:
    blob = " ".join(fragments)
    match = _RAG_TOKEN_PATTERN.search(blob)
    assert match is None, f"RAG vocabulary leaked into non-RAG progress output: {match!r}"


def test_progress_initializes_one_record_per_curriculum_topic() -> None:
    progress = MockProgressAgent().build_progress_state(
        demo.LEARNING_GOAL,
        demo.CURRICULUM,
    )
    topic_ids = [topic.topic_id for week in demo.CURRICULUM.weeks for topic in week.topics]

    assert [item.topic_id for item in progress.topic_progress] == topic_ids
    assert progress.status == ProgressStatus.IN_PROGRESS
    assert progress.current_topic_id == "topic_chunking_strategy"
    assert "retrieval_evaluation" in progress.weak_concepts
    assert "vector_search" in progress.weak_concepts
    assert progress.overall_completion == 0.4
    assert progress.next_recommended_action is not None


def test_progress_marks_low_quiz_topics_as_stuck_and_adaptation_needed() -> None:
    quiz, attempt = _build_quiz_attempt()
    progress = MockProgressAgent().build_progress_state(
        demo.LEARNING_GOAL,
        demo.CURRICULUM,
        attempt,
    )

    by_topic = {item.topic_id: item for item in progress.topic_progress}
    assert quiz.quiz_id == demo.QUIZ_ID
    assert attempt.total_score < 0.65
    assert progress.status == ProgressStatus.ADAPTATION_NEEDED
    assert by_topic["topic_rag_foundations"].status == TopicProgressStatus.STUCK
    assert by_topic["topic_vector_search"].status == TopicProgressStatus.STUCK
    assert {event.topic_id for event in progress.stuck_events} >= {
        "topic_rag_foundations",
        "topic_vector_search",
    }


def test_progress_agent_service_persists_generated_progress_state() -> None:
    container = ApiServiceContainer()
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
    )
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)

    progress = agents.progress.build(goal, curriculum)

    stored = container.progress_service.get_by_id(progress.progress_state_id)
    assert stored == progress
    assert len(stored.topic_progress) == len(
        [topic for week in curriculum.weeks for topic in week.topics],
    )


def test_two_different_goals_each_get_their_own_distinct_progress_state() -> None:
    container = ApiServiceContainer()
    agents = _bundle(container)
    goal_alice = container.goal_service.create(_non_rag_goal(goal_id="goal_alice"))
    curriculum_alice = container.curriculum_service.create(
        _non_rag_curriculum(curriculum_id="curriculum_alice", goal_id="goal_alice"),
    )
    goal_bob = container.goal_service.create(_non_rag_goal(goal_id="goal_bob"))
    curriculum_bob = container.curriculum_service.create(
        _non_rag_curriculum(curriculum_id="curriculum_bob", goal_id="goal_bob"),
    )

    progress_alice = agents.progress.build(
        goal_alice,
        curriculum_alice,
        progress_state_id="progress_alice",
    )
    progress_bob = agents.progress.build(
        goal_bob,
        curriculum_bob,
        progress_state_id="progress_bob",
    )

    assert progress_alice.progress_state_id == "progress_alice"
    assert progress_bob.progress_state_id == "progress_bob"
    assert progress_alice.goal_id == "goal_alice"
    assert progress_bob.goal_id == "goal_bob"
    # The ID-collision defect ADR-0003 traced: without an explicit per-goal
    # ID, learner B's build() would hit DuplicateRecordError on learner A's
    # fixed-ID record and create_or_get would silently return A's data.
    stored_a = container.progress_service.get_by_id("progress_alice")
    stored_b = container.progress_service.get_by_id("progress_bob")
    assert stored_a.goal_id == "goal_alice"
    assert stored_b.goal_id == "goal_bob"


def test_regenerating_updates_the_existing_progress_state_in_place() -> None:
    container = ApiServiceContainer()
    agents = _bundle(container)
    goal = container.goal_service.create(_non_rag_goal(goal_id="goal_regen"))
    curriculum = container.curriculum_service.create(
        _non_rag_curriculum(curriculum_id="curriculum_regen", goal_id="goal_regen"),
    )

    first = agents.progress.build(goal, curriculum, progress_state_id="progress_regen")
    assert first.weak_concepts == []
    assert first.topic_progress[0].status == TopicProgressStatus.NOT_STARTED

    # A real quiz attempt now shows the learner is weak on chord_progressions.
    # Regeneration must update the SAME record with this fresh computation,
    # not create a second record or silently keep the stale first snapshot.
    quiz_attempt = _quiz_attempt(
        goal_id="goal_regen",
        curriculum_id="curriculum_regen",
        weak_concept="chord_progressions",
        score=0.1,
    )
    second = agents.progress.build(
        goal,
        curriculum,
        quiz_attempt,
        progress_state_id="progress_regen",
    )

    assert second.progress_state_id == first.progress_state_id
    assert "chord_progressions" in second.weak_concepts
    assert second.topic_progress[0].status == TopicProgressStatus.STUCK
    stored_records = container.progress_service.list_by_goal_id("goal_regen")
    assert len(stored_records) == 1
    assert stored_records[0] == second


def test_progress_for_a_non_rag_goal_contains_no_rag_content() -> None:
    goal = _non_rag_goal(goal_id="goal_leak_guard")
    curriculum = _non_rag_curriculum(
        curriculum_id="curriculum_leak_guard",
        goal_id="goal_leak_guard",
    )
    quiz_attempt = _quiz_attempt(
        goal_id="goal_leak_guard",
        curriculum_id="curriculum_leak_guard",
        weak_concept="chord_progressions",
        score=0.05,
    )

    progress = MockProgressAgent().build_progress_state(goal, curriculum, quiz_attempt)

    by_topic = {item.topic_id: item for item in progress.topic_progress}
    assert by_topic["topic_chords"].status == TopicProgressStatus.STUCK
    assert progress.stuck_events, "expected a stuck event to actually exercise the leak path"
    for event in progress.stuck_events:
        # The old bug hardcoded ["rag_fundamentals"] here regardless of the
        # topic's real concepts; this proves it now uses the topic's own.
        assert event.concept_ids == ["chord_progressions"]
    blob = progress.model_dump_json().lower()
    _assert_no_rag_vocabulary(blob)
    assert "chord" in blob


def _bundle(container: ApiServiceContainer):
    return build_mock_agent_service_bundle(
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
    )


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


def _quiz_attempt(
    *,
    goal_id: str,
    curriculum_id: str,
    weak_concept: str,
    score: float,
) -> QuizAttemptDTO:
    return QuizAttemptDTO(
        quiz_attempt_id=f"attempt_{goal_id}",
        quiz_id=f"quiz_{goal_id}",
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        answers=[QuizAnswerSubmission(question_id="question_001", selected_options=["A"])],
        total_score=score,
        correct_count=1,
        total_questions=5,
        concept_scores=[
            ConceptQuizScore(
                concept_id=weak_concept,
                score=score,
                correct_count=1,
                total_questions=5,
            ),
        ],
        weak_concepts=[weak_concept],
        submitted_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _build_quiz_attempt() -> tuple[QuizDTO, QuizAttemptDTO]:
    container = ApiServiceContainer()
    quiz_service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress = container.progress_service.create(demo.PROGRESS_STATE)
    return quiz_service.build(goal, curriculum, progress)
