from __future__ import annotations

import re

from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.assessment import ConceptEvidence
from app.schemas.enums import ConceptClassification, KnowledgeMapStatus
from app.schemas.knowledge_map import KnowledgeMapAgentInput


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
    # The first 5 target concepts get a self-rating question each; the demo
    # goal's learner profile marks vector_search/chunking/retrieval_evaluation
    # as weak areas (self-rated low) and leaves rag_fundamentals/embeddings
    # neutral. The profile's strengths (python_basics, machine_learning_basics,
    # api_basics) are never asked about but are still added as evidence.
    assert "rag_fundamentals" in knowledge_map.developing_concepts
    assert "embeddings" in knowledge_map.developing_concepts
    assert "retrieval_evaluation" in knowledge_map.weak_concepts
    assert "vector_search" in knowledge_map.weak_concepts
    assert "chunking" in knowledge_map.weak_concepts
    assert "python_basics" in knowledge_map.strong_concepts
    assert "machine_learning_basics" in knowledge_map.strong_concepts
    assert "api_basics" in knowledge_map.strong_concepts
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
    assert concept_by_id["retrieval_evaluation"].recommended_action
    assert concept_by_id["retrieval_evaluation"].label == "Retrieval Evaluation"
    assert concept_by_id["retrieval_evaluation"].prerequisites == []
    assert container.knowledge_map_service.get_by_id(demo.KNOWLEDGE_MAP_ID) == (
        knowledge_map
    )


_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def test_knowledge_map_for_a_non_rag_goal_does_not_inject_rag_missing_concepts() -> None:
    payload = KnowledgeMapAgentInput(
        goal_text="Learn classical guitar for a wedding performance",
        assessment_answers=[],
        concept_evidence=[
            ConceptEvidence(concept_id="chord_progressions", score=0.25, evidence=["shaky"]),
            ConceptEvidence(concept_id="fingerpicking", score=0.15, evidence=["new to it"]),
        ],
    )

    output = build_knowledge_map_output(payload)

    concept_ids = {concept.concept_id for concept in output.concepts}
    assert concept_ids == {"chord_progressions", "fingerpicking"}


def test_knowledge_map_for_a_synthetic_non_rag_goal_contains_no_rag_vocabulary() -> None:
    payload = KnowledgeMapAgentInput(
        goal_text="Learn to play classical guitar for weddings",
        assessment_answers=[],
        concept_evidence=[
            ConceptEvidence(
                concept_id="music_theory_basics",
                score=0.15,
                evidence=["Could not name the notes in a major scale."],
            ),
            ConceptEvidence(
                concept_id="fingerpicking_technique",
                score=0.30,
                evidence=["Struggles with alternating bass lines."],
            ),
        ],
    )

    output = build_knowledge_map_output(payload)

    concept_ids = {concept.concept_id for concept in output.concepts}
    assert concept_ids == {"music_theory_basics", "fingerpicking_technique"}

    serialized = output.model_dump_json()
    assert not _RAG_TOKEN_PATTERN.search(serialized), serialized

    for concept in output.concepts:
        assert concept.prerequisites == []
