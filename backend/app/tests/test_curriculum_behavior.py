from __future__ import annotations

from app.agents.mock import MockCurriculumAgent
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput


def test_curriculum_generation_prioritizes_weak_and_missing_concepts() -> None:
    output = _build_curriculum_output()

    assert CurriculumAgentOutput.model_validate(output) == output
    assert output.duration_weeks == 4
    assert len(output.weeks) == 4
    assert all(week.estimated_hours <= 7 for week in output.weeks)

    topics = [topic for week in output.weeks for topic in week.topics]
    topic_ids = [topic.topic_id for topic in topics]
    topic_concepts = {concept for topic in topics for concept in topic.concept_ids}

    assert "topic_retrieval_metrics" in topic_ids
    assert "topic_vector_search" in topic_ids
    assert "topic_reranking_intro" in topic_ids
    assert "topic_production_rag" in topic_ids
    assert {
        "retrieval_evaluation",
        "vector_search",
        "reranking",
        "production_rag_failures",
    } <= topic_concepts
    assert _sequence(topic_ids, "topic_embeddings_review") < _sequence(
        topic_ids,
        "topic_vector_search",
    )
    assert _sequence(topic_ids, "topic_retrieval_metrics") < _sequence(
        topic_ids,
        "topic_reranking_intro",
    )


def test_curriculum_agent_service_persists_generated_curriculum() -> None:
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
    knowledge_map = container.knowledge_map_service.create(demo.KNOWLEDGE_MAP)

    curriculum = agents.curriculum.build(goal, knowledge_map)

    stored = container.curriculum_service.get_by_id(curriculum.curriculum_id)
    stored_concepts = {
        concept
        for week in stored.weeks
        for topic in week.topics
        for concept in topic.concept_ids
    }
    assert stored == curriculum
    assert "reranking" in stored_concepts
    assert "production_rag_failures" in stored_concepts


def _build_curriculum_output() -> CurriculumAgentOutput:
    payload = CurriculumAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        learner_profile=demo.LEARNER_PROFILE,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=4,
        hours_per_week=7,
    )
    return MockCurriculumAgent().build_curriculum(payload)


def _sequence(topic_ids: list[str], topic_id: str) -> int:
    return topic_ids.index(topic_id)
