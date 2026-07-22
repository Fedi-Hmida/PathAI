from __future__ import annotations

import re

from app.agents.mock import MockCurriculumAgent
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.enums import ConceptClassification
from app.schemas.knowledge_map import ConceptMasteryDTO

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def _assert_no_rag_vocabulary(*fragments: str) -> None:
    blob = " ".join(fragments)
    match = _RAG_TOKEN_PATTERN.search(blob)
    assert match is None, f"RAG vocabulary leaked into non-RAG curriculum output: {match!r}"


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


def test_curriculum_for_a_non_rag_goal_contains_no_rag_content() -> None:
    non_rag_concepts = [
        ConceptMasteryDTO(
            concept_id="chord_progressions",
            label="Chord progressions",
            mastery_score=0.2,
            classification=ConceptClassification.WEAK,
            evidence=["Struggled with basic chord transitions."],
        ),
        ConceptMasteryDTO(
            concept_id="fingerpicking",
            label="Fingerpicking",
            mastery_score=0.1,
            classification=ConceptClassification.MISSING,
        ),
    ]
    knowledge_map = demo.KNOWLEDGE_MAP.model_copy(
        update={
            "concepts": non_rag_concepts,
            "strong_concepts": [],
            "developing_concepts": [],
            "weak_concepts": ["chord_progressions"],
            "missing_concepts": ["fingerpicking"],
        },
    )
    payload = CurriculumAgentInput(
        goal_text="Learn classical guitar for a wedding performance",
        learner_profile=demo.LEARNER_PROFILE.model_copy(
            update={"weak_areas": [], "strengths": []},
        ),
        knowledge_map=knowledge_map,
        duration_weeks=3,
        hours_per_week=5,
    )

    output = MockCurriculumAgent().build_curriculum(payload)

    assert CurriculumAgentOutput.model_validate(output) == output
    blob = output.model_dump_json().lower()
    _assert_no_rag_vocabulary(blob)
    assert "guitar" in blob or "wedding" in blob


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
