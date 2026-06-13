import pytest

from app.assessment.schemas import KnowledgeMap
from app.critic.schemas import CriticCurriculumOnlyRequest, CriticReviewRequest
from app.critic.service import CriticService
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.rag.schemas import CurriculumResourceAttachmentRequest
from app.rag.service import ResourceService


def _curriculum() -> CurriculumPlan:
    return build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems",
            timeline_weeks=4,
            hours_per_week=8,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Chunking", "Reranking"],
                recommended_level="beginner",
                confidence_score=0.84,
                assessment_notes=["Critic service test map."],
            ),
        )
    )


def _review_request(required_resources_per_topic: int = 1) -> CriticReviewRequest:
    curriculum = _curriculum()
    resources = ResourceService().retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )
    return CriticReviewRequest(
        curriculum=curriculum,
        resource_attachment=resources,
        required_resources_per_topic=required_resources_per_topic,
    )


@pytest.mark.asyncio
async def test_critic_approves_valid_curriculum_with_resources() -> None:
    review = await CriticService().review_curriculum_with_resources(_review_request())

    assert review.approved is True
    assert review.decision == "approved"
    assert review.overall_quality_score >= 0.78
    assert review.curriculum_issues == []


@pytest.mark.asyncio
async def test_critic_rejects_missing_resource_coverage() -> None:
    request = _review_request(required_resources_per_topic=2)

    review = await CriticService().review_curriculum_with_resources(request)

    assert review.approved is False
    assert review.decision == "rejected"
    assert any(issue.code == "resource_coverage_gap" for issue in review.resource_issues)
    assert review.revision_instructions


@pytest.mark.asyncio
async def test_critic_rejects_weekly_hour_overrun() -> None:
    request = _review_request()
    first_week = request.curriculum.weeks[0].model_copy(update={"estimated_hours": 12.0})
    curriculum = request.curriculum.model_copy(
        update={"weeks": [first_week, *request.curriculum.weeks[1:]]}
    )

    review = await CriticService().review_curriculum_with_resources(
        request.model_copy(update={"curriculum": curriculum})
    )

    assert review.approved is False
    assert any(issue.code == "weekly_hours_exceeded" for issue in review.curriculum_issues)


@pytest.mark.asyncio
async def test_critic_rejects_missing_project_final_week() -> None:
    request = _review_request()
    final_week = request.curriculum.weeks[-1].model_copy(update={"project_or_application": False})
    curriculum = request.curriculum.model_copy(
        update={"weeks": [*request.curriculum.weeks[:-1], final_week]}
    )

    review = await CriticService().review_curriculum_with_resources(
        request.model_copy(update={"curriculum": curriculum})
    )

    assert review.approved is False
    assert any(issue.code == "missing_project_final_week" for issue in review.curriculum_issues)


@pytest.mark.asyncio
async def test_critic_detects_low_quality_why_this_explanation() -> None:
    request = _review_request()
    attachment = request.resource_attachment
    assert attachment is not None
    first_attachment = attachment.attachments[0]
    first_resource = first_attachment.resources[0].model_copy(
        update={"why_recommended": "Good."}
    )
    updated_attachment = first_attachment.model_copy(
        update={"resources": [first_resource, *first_attachment.resources[1:]]}
    )
    resources = attachment.model_copy(
        update={"attachments": [updated_attachment, *attachment.attachments[1:]]}
    )

    review = await CriticService().review_curriculum_with_resources(
        request.model_copy(update={"resource_attachment": resources})
    )

    assert any(issue.code == "why_this_too_generic" for issue in review.resource_issues)
    assert review.overall_quality_score < 1.0


@pytest.mark.asyncio
async def test_critic_detects_resource_difficulty_mismatch() -> None:
    request = _review_request()
    attachment = request.resource_attachment
    assert attachment is not None
    first_attachment = attachment.attachments[0]
    first_resource = first_attachment.resources[0].model_copy(update={"difficulty": "advanced"})
    updated_attachment = first_attachment.model_copy(
        update={"resources": [first_resource, *first_attachment.resources[1:]]}
    )
    resources = attachment.model_copy(
        update={"attachments": [updated_attachment, *attachment.attachments[1:]]}
    )

    review = await CriticService().review_curriculum_with_resources(
        request.model_copy(update={"resource_attachment": resources})
    )

    assert any(issue.code == "resource_difficulty_mismatch" for issue in review.resource_issues)


@pytest.mark.asyncio
async def test_critic_forces_auto_approval_at_max_revisions() -> None:
    request = _review_request(required_resources_per_topic=2).model_copy(
        update={"revision_count": 3, "max_revisions": 3}
    )

    review = await CriticService().review_curriculum_with_resources(request)

    assert review.approved is True
    assert review.auto_approved is True
    assert review.decision == "auto_approved"
    assert review.warnings


@pytest.mark.asyncio
async def test_curriculum_only_review_skips_resource_checks() -> None:
    curriculum = _curriculum()

    review = await CriticService().review_curriculum(
        request=CriticCurriculumOnlyRequest(curriculum=curriculum)
    )

    assert review.approved is True
    assert review.resource_coverage_review.resources_reviewed is False
    assert review.warnings
