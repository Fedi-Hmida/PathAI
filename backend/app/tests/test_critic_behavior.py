from __future__ import annotations

from app.agents.mock import MockCriticAgent, MockCurriculumAgent, MockResourceAgent
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumDTO
from app.schemas.enums import CriticPassStatus
from app.schemas.resource import ResourceAgentInput, ResourceAttachmentDTO


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
    assert output.pass_status == CriticPassStatus.PASS
    assert output.dimension_scores.coverage >= 0.9
    assert output.dimension_scores.resource_relevance >= 0.8
    assert output.issues == []
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
    assert review.pass_status == CriticPassStatus.PASS


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
