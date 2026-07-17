from __future__ import annotations

from app.agents.mock import MockProgressAgent, MockQuizAgent
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.quiz import QuizAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.enums import ProgressStatus, TopicProgressStatus
from app.schemas.quiz import QuizAttemptDTO, QuizDTO


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


def _build_quiz_attempt() -> tuple[QuizDTO, QuizAttemptDTO]:
    container = ApiServiceContainer()
    quiz_service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress = container.progress_service.create(demo.PROGRESS_STATE)
    return quiz_service.build(goal, curriculum, progress)
