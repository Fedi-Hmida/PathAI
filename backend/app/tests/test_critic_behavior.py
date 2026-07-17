from __future__ import annotations

import re

from app.agents.deterministic.critic import build_critic_output
from app.agents.mock import MockCriticAgent, MockCurriculumAgent, MockResourceAgent
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import (
    CurriculumAgentInput,
    CurriculumDTO,
    CurriculumTopicDTO,
    CurriculumWeekDTO,
)
from app.schemas.enums import (
    ConceptClassification,
    CriticPassStatus,
    CurriculumStatus,
    DifficultyLevel,
    KnowledgeMapStatus,
)
from app.schemas.knowledge_map import ConceptMasteryDTO, KnowledgeMapDTO
from app.schemas.resource import ResourceAgentInput, ResourceAttachmentDTO

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|vector[ _]search|embedding|chunking)\b",
    re.IGNORECASE,
)


def _assert_no_rag_vocabulary(*fragments: str) -> None:
    blob = " ".join(fragments)
    match = _RAG_TOKEN_PATTERN.search(blob)
    assert match is None, f"RAG vocabulary leaked into non-RAG critic output: {match!r}"


def test_deterministic_critic_is_topic_general_for_a_non_rag_goal() -> None:
    """The prerequisite-gap check must derive from the knowledge map's own
    per-concept data, never a fixed RAG-specific table - so a non-RAG goal's
    critic output (including an intentional prerequisite gap, the case most
    likely to leak fixture vocabulary) contains zero RAG tokens."""
    knowledge_map = KnowledgeMapDTO(
        knowledge_map_id="kmap_guitar",
        goal_id="goal_guitar",
        assessment_session_id="assessment_guitar",
        run_id="run_guitar",
        status=KnowledgeMapStatus.ACTIVE,
        concepts=[
            ConceptMasteryDTO(
                concept_id="music_theory_basics",
                label="Music theory basics",
                mastery_score=0.8,
                classification=ConceptClassification.STRONG,
                prerequisites=[],
            ),
            ConceptMasteryDTO(
                concept_id="finger_picking_technique",
                label="Finger-picking technique",
                mastery_score=0.3,
                classification=ConceptClassification.WEAK,
                prerequisites=["music_theory_basics"],
            ),
            ConceptMasteryDTO(
                concept_id="wedding_repertoire",
                label="Wedding repertoire",
                mastery_score=0.1,
                classification=ConceptClassification.MISSING,
                prerequisites=["finger_picking_technique"],
            ),
        ],
        strong_concepts=["music_theory_basics"],
        weak_concepts=["finger_picking_technique"],
        missing_concepts=["wedding_repertoire"],
        confidence=0.7,
        summary="Strong on theory, needs finger-picking and repertoire work.",
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )
    curriculum = CurriculumDTO(
        curriculum_id="curriculum_guitar",
        goal_id="goal_guitar",
        knowledge_map_id="kmap_guitar",
        run_id="run_guitar",
        status=CurriculumStatus.ACTIVE,
        title="Classical Guitar for a Wedding Performance",
        duration_weeks=2,
        target_outcomes=["Perform a short classical guitar set at a wedding."],
        created_at=demo.NOW,
        updated_at=demo.NOW,
        weeks=[
            CurriculumWeekDTO(
                week_id="week_intro",
                week_number=1,
                theme="Foundations",
                estimated_hours=5.0,
                learning_outcomes=["Read basic notation and rhythm."],
                topics=[
                    CurriculumTopicDTO(
                        topic_id="topic_theory",
                        title="Music theory basics",
                        description="Notation, rhythm, and key signatures.",
                        concept_ids=["music_theory_basics"],
                        difficulty=DifficultyLevel.BEGINNER,
                        estimated_hours=5.0,
                        learning_outcomes=["Read basic notation."],
                        sequence_order=1,
                    ),
                ],
            ),
            CurriculumWeekDTO(
                week_id="week_repertoire",
                week_number=2,
                theme="Performance repertoire",
                estimated_hours=5.0,
                learning_outcomes=["Play a wedding-appropriate piece."],
                topics=[
                    # Deliberately skips a dedicated finger-picking topic, so
                    # the knowledge map's own prerequisite chain
                    # (wedding_repertoire -> finger_picking_technique) is
                    # violated - the case most likely to leak stale fixture
                    # vocabulary if the detox were incomplete.
                    CurriculumTopicDTO(
                        topic_id="topic_repertoire",
                        title="Wedding repertoire",
                        description="Learn a short classical piece for the ceremony.",
                        concept_ids=["wedding_repertoire"],
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        estimated_hours=5.0,
                        learning_outcomes=["Perform a full piece from memory."],
                        sequence_order=2,
                    ),
                ],
            ),
        ],
    )

    output = build_critic_output(
        CriticAgentInput(
            goal_text="Learn classical guitar for a wedding performance",
            knowledge_map=knowledge_map,
            curriculum=curriculum,
            resource_attachments=[],
        ),
    )

    assert any("Prerequisite gap" in issue for issue in output.issues)
    _assert_no_rag_vocabulary(
        *output.strengths,
        *output.issues,
        *output.revision_recommendations,
    )


def test_critic_review_scores_generated_curriculum_and_resources() -> None:
    curriculum = _dynamic_curriculum()
    attachments = _dynamic_attachments(curriculum)

    output = MockCriticAgent().review_curriculum(
        CriticAgentInput(
            goal_text=demo.CANONICAL_GOAL_TEXT,
            knowledge_map=demo.KNOWLEDGE_MAP,
            curriculum=curriculum,
            resource_attachments=attachments,
        ),
    )

    assert CriticAgentOutput.model_validate(output) == output
    assert output.overall_score >= 0.85
    assert output.pass_status == CriticPassStatus.PASS_WITH_WARNINGS
    assert output.dimension_scores.coverage >= 0.9
    assert output.dimension_scores.resource_relevance >= 0.8
    # Prerequisite gaps are now derived from the knowledge map's own
    # per-concept prerequisite data (ConceptMasteryDTO.prerequisites), which
    # is more complete than the old hardcoded RAG-specific table this
    # replaced - it correctly surfaces that the generated curriculum places
    # two topics ahead of concepts the knowledge map says they depend on.
    assert all("Prerequisite gap" in issue for issue in output.issues)
    assert len(output.issues) == 2
    assert any("Weak and missing concepts" in strength for strength in output.strengths)


def test_critic_review_detects_overload_and_missing_resources() -> None:
    curriculum = _dynamic_curriculum()
    overloaded_week = curriculum.weeks[0].model_copy(
        update={"estimated_hours": 12.0},
        deep=True,
    )
    weak_curriculum = curriculum.model_copy(
        update={"weeks": [overloaded_week, *curriculum.weeks[1:]]},
        deep=True,
    )

    output = MockCriticAgent().review_curriculum(
        CriticAgentInput(
            goal_text=demo.CANONICAL_GOAL_TEXT,
            knowledge_map=demo.KNOWLEDGE_MAP,
            curriculum=weak_curriculum,
            resource_attachments=[],
        ),
    )

    assert output.pass_status == CriticPassStatus.PASS_WITH_WARNINGS
    assert any("workload" in issue for issue in output.issues)
    assert any("Resource diversity" in issue for issue in output.issues)
    assert any("No resource attachments" in issue for issue in output.issues)
    assert output.revision_recommendations


def test_critic_agent_service_persists_review() -> None:
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
    attachments = agents.resource.attach(curriculum, knowledge_map)

    review = agents.critic.review(goal, knowledge_map, curriculum, attachments)

    assert container.critic_service.get_by_id(review.critic_review_id) == review
    assert review.overall_score >= 0.85
    assert review.pass_status == CriticPassStatus.PASS_WITH_WARNINGS


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


def _dynamic_attachments(curriculum: CurriculumDTO) -> list[ResourceAttachmentDTO]:
    output = MockResourceAgent().attach_resources(
        ResourceAgentInput(
            curriculum=curriculum,
            knowledge_map=demo.KNOWLEDGE_MAP,
            corpus_resources=demo.RESOURCE_CORPUS,
            max_resources_per_topic=3,
        ),
    )
    return output.attachments
