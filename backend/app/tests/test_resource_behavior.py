from __future__ import annotations

import re

from app.agents.deterministic.resource import build_resource_output
from app.agents.mock import MockCurriculumAgent, MockResourceAgent
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import (
    CurriculumAgentInput,
    CurriculumDTO,
    CurriculumTopicDTO,
    CurriculumWeekDTO,
)
from app.schemas.enums import CurriculumStatus, DifficultyLevel
from app.schemas.resource import ResourceAgentInput, ResourceAgentOutput

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def _assert_no_rag_vocabulary(*fragments: str) -> None:
    blob = " ".join(fragments)
    match = _RAG_TOKEN_PATTERN.search(blob)
    assert match is None, f"RAG vocabulary leaked into non-RAG resource output: {match!r}"


def test_resource_attachment_covers_curriculum_topics_with_diversity() -> None:
    curriculum = _dynamic_curriculum()
    output = MockResourceAgent().attach_resources(
        ResourceAgentInput(
            curriculum=curriculum,
            knowledge_map=demo.KNOWLEDGE_MAP,
            corpus_resources=demo.RESOURCE_CORPUS,
            max_resources_per_topic=3,
        ),
    )

    assert ResourceAgentOutput.model_validate(output) == output
    assert output.coverage_summary.topics_without_resources == 0
    assert output.coverage_summary.resource_type_diversity == 1.0
    assert output.coverage_summary.average_relevance >= 0.8

    categories = {
        attachment.diversity_category
        for attachment in output.attachments
        if attachment.diversity_category
    }
    assert {
        "documentation",
        "paper",
        "video",
        "code_example",
        "exercise",
    } <= categories
    assert any(
        attachment.topic_id == "topic_retrieval_metrics"
        and attachment.resource_id == "resource_retrieval_metrics"
        for attachment in output.attachments
    )
    assert any(
        attachment.topic_id == "topic_reranking_intro"
        and attachment.resource_id == "resource_reranking_paper"
        for attachment in output.attachments
    )


def test_resource_agent_service_persists_generated_attachments() -> None:
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

    attachments = agents.resource.attach(curriculum, knowledge_map)

    stored = container.resource_service.list_attachments_by_curriculum_id(
        curriculum.curriculum_id,
    )
    assert stored == attachments
    assert len(stored) >= len([topic for week in curriculum.weeks for topic in week.topics])


def test_attachment_ids_are_goal_scoped_and_never_collide_across_goals() -> None:
    """Two different goals whose curricula happen to produce the identical
    topic_id - the realistic case, since every non-RAG goal's deterministic
    curriculum collapses to the same `topic_general_foundations` fallback
    topic (`deterministic/curriculum.py::_generic_fallback_topic`) - and
    match the same corpus resource must get distinct, correctly-scoped
    attachment records. Direct proof of the `_attachment_id` goal-scoping
    fix; before it, these two goals collided on the identical ID."""
    resource = demo.RESOURCE_CORPUS[0]
    curriculum_a = _minimal_curriculum(
        curriculum_id="curriculum_alpha_test",
        goal_id="goal_alpha_test",
    )
    curriculum_b = _minimal_curriculum(
        curriculum_id="curriculum_beta_test",
        goal_id="goal_beta_test",
    )

    output_a = build_resource_output(
        ResourceAgentInput(
            curriculum=curriculum_a,
            knowledge_map=demo.KNOWLEDGE_MAP,
            corpus_resources=[resource],
        ),
    )
    output_b = build_resource_output(
        ResourceAgentInput(
            curriculum=curriculum_b,
            knowledge_map=demo.KNOWLEDGE_MAP,
            corpus_resources=[resource],
        ),
    )

    assert len(output_a.attachments) == 1
    assert len(output_b.attachments) == 1
    attachment_a, attachment_b = output_a.attachments[0], output_b.attachments[0]
    assert attachment_a.topic_id == attachment_b.topic_id == "topic_shared"
    assert attachment_a.resource_id == attachment_b.resource_id == resource.resource_id
    assert attachment_a.goal_id == "goal_alpha_test"
    assert attachment_b.goal_id == "goal_beta_test"
    assert attachment_a.attachment_id != attachment_b.attachment_id
    assert "alpha_test" in attachment_a.attachment_id
    assert "beta_test" in attachment_b.attachment_id


def test_non_rag_goal_gets_real_matches_from_the_curated_non_rag_corpus_entries() -> None:
    """Big_Audit Step 12's corpus-diversity decision: a genuinely non-RAG
    goal (mirroring the real deterministic fallback-topic shape) matches the
    curated guitar entries added to the corpus via real tag overlap - no
    scoring-math change, no fabricated match."""
    curriculum = _minimal_curriculum(
        curriculum_id="curriculum_guitar_match_test",
        goal_id="goal_guitar_match_test",
        topic_title="Foundations for: Learn classical guitar for a wedding performance",
        concept_ids=["general_concepts"],
    )

    output = build_resource_output(
        ResourceAgentInput(
            curriculum=curriculum,
            knowledge_map=demo.KNOWLEDGE_MAP,
            corpus_resources=demo.RESOURCE_CORPUS,
        ),
    )

    matched_resource_ids = {attachment.resource_id for attachment in output.attachments}
    assert "resource_guitar_fundamentals" in matched_resource_ids
    assert matched_resource_ids.isdisjoint(
        {"resource_watercolor_fundamentals", "resource_painting_fundamentals"},
    )


def test_genuinely_non_matching_goal_gets_an_honest_empty_result() -> None:
    """A goal with nothing in the corpus for it (deterministic RAG corpus
    plus the curated guitar/watercolor additions) gets zero attachments and
    an honest warning, never a fabricated placeholder match."""
    curriculum = _minimal_curriculum(
        curriculum_id="curriculum_no_match_test",
        goal_id="goal_no_match_test",
        topic_title="Foundations for: Learn Mandarin calligraphy for a museum exhibit",
        concept_ids=["general_concepts"],
    )

    output = build_resource_output(
        ResourceAgentInput(
            curriculum=curriculum,
            knowledge_map=demo.KNOWLEDGE_MAP,
            corpus_resources=demo.RESOURCE_CORPUS,
        ),
    )

    assert output.attachments == []
    assert output.coverage_summary.topics_with_resources == 0
    assert output.coverage_summary.topics_without_resources == 1
    assert output.coverage_summary.average_relevance == 0.0
    assert any("No deterministic resource match" in warning for warning in output.warnings)


def test_non_rag_goal_resource_output_carries_no_rag_vocabulary() -> None:
    curriculum = _minimal_curriculum(
        curriculum_id="curriculum_guitar_rag_guard_test",
        goal_id="goal_guitar_rag_guard_test",
        topic_title="Foundations for: Learn classical guitar for a wedding performance",
        concept_ids=["general_concepts"],
    )

    output = build_resource_output(
        ResourceAgentInput(
            curriculum=curriculum,
            knowledge_map=demo.KNOWLEDGE_MAP,
            corpus_resources=demo.RESOURCE_CORPUS,
        ),
    )

    assert output.attachments != []
    _assert_no_rag_vocabulary(
        *(attachment.selection_reason for attachment in output.attachments),
        *output.warnings,
    )


def _minimal_curriculum(
    *,
    curriculum_id: str,
    goal_id: str,
    topic_id: str = "topic_shared",
    topic_title: str = "Foundations",
    concept_ids: list[str] | None = None,
) -> CurriculumDTO:
    topic = CurriculumTopicDTO(
        topic_id=topic_id,
        title=topic_title,
        description="A minimal topic built directly for a resource-matching test.",
        concept_ids=concept_ids or ["rag_fundamentals"],
        difficulty=DifficultyLevel.BEGINNER,
        estimated_hours=2.0,
        learning_outcomes=["Review the topic."],
        sequence_order=1,
    )
    return CurriculumDTO(
        curriculum_id=curriculum_id,
        goal_id=goal_id,
        knowledge_map_id=demo.KNOWLEDGE_MAP_ID,
        run_id=demo.RUN_ID,
        status=CurriculumStatus.ACTIVE,
        title=topic_title,
        duration_weeks=1,
        weeks=[
            CurriculumWeekDTO(
                week_id="week_shared",
                week_number=1,
                theme="Foundations",
                topics=[topic],
                estimated_hours=2.0,
                learning_outcomes=["Review the topic."],
            ),
        ],
        target_outcomes=["Make measurable progress."],
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _dynamic_curriculum() -> CurriculumDTO:
    output = MockCurriculumAgent().build_curriculum(
        CurriculumAgentInput(
            goal_text=demo.CANONICAL_GOAL_TEXT,
            learner_profile=demo.LEARNER_PROFILE,
            knowledge_map=demo.KNOWLEDGE_MAP,
            duration_weeks=4,
            hours_per_week=7,
        ),
    )
    return demo.CURRICULUM.model_copy(
        update={
            "title": output.title,
            "duration_weeks": output.duration_weeks,
            "weeks": output.weeks,
            "target_outcomes": output.target_outcomes,
            "assumptions": output.assumptions,
        },
        deep=True,
    )
