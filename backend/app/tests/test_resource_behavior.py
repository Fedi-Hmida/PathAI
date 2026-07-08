from __future__ import annotations

from app.agents.mock import MockCurriculumAgent, MockResourceAgent
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumAgentInput, CurriculumDTO
from app.schemas.resource import ResourceAgentInput, ResourceAgentOutput


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
