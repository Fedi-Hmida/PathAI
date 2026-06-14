import pytest

from app.assessment.schemas import KnowledgeMap
from app.critic.schemas import CriticCurriculumOnlyRequest, CriticReviewRequest
from app.critic.service import CriticService, RepositoryBackedCriticStore
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.evaluation.schemas import EvaluationRunRequest
from app.evaluation.service import EvaluationService, RepositoryBackedEvaluationStore
from app.rag.schemas import CurriculumResourceAttachmentRequest
from app.rag.service import RepositoryBackedResourceStore, ResourceService
from app.repositories import (
    FakeCriticRepository,
    FakeEvaluationRepository,
    FakeResourceRepository,
)


def _curriculum() -> CurriculumPlan:
    return build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems for a graduation project",
            timeline_weeks=4,
            hours_per_week=6,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Chunking", "Reranking"],
                recommended_level="intermediate",
                confidence_score=0.86,
                assessment_notes=["Critic/resource/evaluation migration fixture."],
            ),
        )
    )


@pytest.mark.asyncio
async def test_critic_service_saves_reviews_with_injected_repository() -> None:
    repository = FakeCriticRepository()
    service = CriticService(repository=repository)
    curriculum = _curriculum()
    resources = ResourceService().retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )

    review = await service.review_curriculum_with_resources(
        CriticReviewRequest(
            curriculum=curriculum,
            resource_attachment=resources,
            required_resources_per_topic=1,
        )
    )
    latest = service.get_latest_review(curriculum.curriculum_id)
    history = service.list_reviews_for_curriculum(curriculum.curriculum_id)

    assert review.curriculum_id == curriculum.curriculum_id
    assert latest is not None
    assert latest.review_id == review.review_id
    assert [stored.review_id for stored in history] == [review.review_id]


@pytest.mark.asyncio
async def test_repository_backed_critic_store_keeps_clear_compatibility() -> None:
    repository = FakeCriticRepository()
    service = CriticService(store=RepositoryBackedCriticStore(repository))
    curriculum = _curriculum()

    review = await service.review_curriculum(
        CriticCurriculumOnlyRequest(curriculum=curriculum)
    )
    assert service.get_latest_review(curriculum.curriculum_id) is not None

    service.store.clear()
    assert service.get_latest_review(curriculum.curriculum_id) is None
    assert service.list_reviews_for_curriculum(curriculum.curriculum_id) == []
    assert repository.get_latest_review(curriculum.curriculum_id) is None
    assert review.curriculum_id == curriculum.curriculum_id


def test_resource_service_persists_catalog_and_curriculum_attachment() -> None:
    repository = FakeResourceRepository()
    service = ResourceService(repository=repository)
    curriculum = _curriculum()

    summary = service.get_resource_catalog_summary()
    attachment = service.retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )
    stored_attachment = service.get_attachment_for_curriculum(curriculum.curriculum_id)

    assert summary.total_resources > 0
    assert len(repository.list_catalog()) == summary.total_resources
    assert stored_attachment is not None
    assert stored_attachment.curriculum_id == curriculum.curriculum_id
    assert len(stored_attachment.attachments) == len(attachment.attachments)


def test_repository_backed_resource_store_keeps_clear_compatibility() -> None:
    repository = FakeResourceRepository()
    service = ResourceService(store=RepositoryBackedResourceStore(repository))
    curriculum = _curriculum()

    service.retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=1)
    )
    assert service.get_attachment_for_curriculum(curriculum.curriculum_id) is not None

    service.store.clear()
    assert service.get_attachment_for_curriculum(curriculum.curriculum_id) is None
    assert repository.list_catalog() == []


def test_evaluation_service_saves_lists_and_fetches_reports() -> None:
    repository = FakeEvaluationRepository()
    service = EvaluationService(repository=repository)

    report = service.run_sample_evaluation(EvaluationRunRequest())
    listed = service.list_reports(report.dataset_name)
    fetched = service.get_report(report.evaluation_id)

    assert fetched is not None
    assert fetched.evaluation_id == report.evaluation_id
    assert [stored.evaluation_id for stored in listed] == [report.evaluation_id]
    assert "synthetic" in " ".join(report.limitations).lower()


def test_repository_backed_evaluation_store_keeps_clear_compatibility() -> None:
    repository = FakeEvaluationRepository()
    service = EvaluationService(store=RepositoryBackedEvaluationStore(repository))

    report = service.run_sample_evaluation(EvaluationRunRequest())
    assert service.get_report(report.evaluation_id) is not None

    service.store.clear()
    assert service.get_report(report.evaluation_id) is None
    assert service.list_reports() == []
