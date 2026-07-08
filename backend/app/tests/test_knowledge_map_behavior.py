from __future__ import annotations

from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.enums import ConceptClassification, KnowledgeMapStatus


def test_knowledge_map_is_generated_from_assessment_evidence() -> None:
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
    assessment = agents.assessment.run_diagnostic(goal)
    answers = container.assessment_service.list_answers_by_session_id(
        assessment.assessment_session_id,
    )
    knowledge_map = agents.knowledge_map.build(goal, assessment, answers)

    assert knowledge_map.status == KnowledgeMapStatus.ACTIVE
    assert knowledge_map.confidence >= 0.70
    assert "rag_fundamentals" in knowledge_map.strong_concepts
    assert "chunking" in knowledge_map.developing_concepts
    assert "retrieval_evaluation" in knowledge_map.weak_concepts
    assert "vector_search" in knowledge_map.weak_concepts
    assert "reranking" in knowledge_map.missing_concepts
    assert "production_rag_failures" in knowledge_map.missing_concepts
    assert "Recommended level: intermediate" in knowledge_map.summary


def test_knowledge_map_concepts_are_schema_valid_and_curriculum_ready() -> None:
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
    assessment = agents.assessment.run_diagnostic(goal)
    answers = container.assessment_service.list_answers_by_session_id(
        assessment.assessment_session_id,
    )
    knowledge_map = agents.knowledge_map.build(goal, assessment, answers)

    concept_by_id = {
        concept.concept_id: concept
        for concept in knowledge_map.concepts
    }
    assert concept_by_id["retrieval_evaluation"].classification == (
        ConceptClassification.WEAK
    )
    assert concept_by_id["reranking"].classification == ConceptClassification.MISSING
    assert concept_by_id["retrieval_evaluation"].recommended_action
    assert concept_by_id["reranking"].prerequisites == ["retrieval_evaluation"]
    assert container.knowledge_map_service.get_by_id(demo.KNOWLEDGE_MAP_ID) == (
        knowledge_map
    )
