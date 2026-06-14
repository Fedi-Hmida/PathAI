from typing import Protocol

from app.agents.constants import CriticDecision
from app.agents.state import CriticReview as GraphCriticReview
from app.critic.llm import review_with_mock_llm
from app.critic.rubric import get_rubric_summary, review_with_deterministic_rubric
from app.critic.schemas import (
    CriticCurriculumOnlyRequest,
    CriticReviewRequest,
    CriticReviewResult,
    CriticRubricSummary,
)
from app.repositories import CriticRepository, FakeCriticRepository


class CriticStore(Protocol):
    def save(self, review: CriticReviewResult) -> None:
        ...

    def latest(self, curriculum_id: str) -> CriticReviewResult | None:
        ...

    def list_for_curriculum(self, curriculum_id: str) -> list[CriticReviewResult]:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedCriticStore:
    def __init__(self, repository: CriticRepository | None = None) -> None:
        self.repository = repository or FakeCriticRepository()

    def save(self, review: CriticReviewResult) -> None:
        self.repository.save_review(review.model_dump(mode="json"))

    def latest(self, curriculum_id: str) -> CriticReviewResult | None:
        payload = self.repository.get_latest_review(curriculum_id)
        if payload is None:
            return None
        return CriticReviewResult.model_validate(payload)

    def list_for_curriculum(self, curriculum_id: str) -> list[CriticReviewResult]:
        return [
            CriticReviewResult.model_validate(payload)
            for payload in self.repository.list_reviews_for_curriculum(curriculum_id)
        ]

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryCriticStore(RepositoryBackedCriticStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeCriticRepository())


class CriticService:
    def __init__(
        self,
        store: CriticStore | None = None,
        repository: CriticRepository | None = None,
    ) -> None:
        self.store = store or RepositoryBackedCriticStore(repository)

    async def review_curriculum(
        self,
        request: CriticCurriculumOnlyRequest,
    ) -> CriticReviewResult:
        critic_request = CriticReviewRequest(
            curriculum=request.curriculum,
            revision_count=request.revision_count,
            max_revisions=request.max_revisions,
            use_mock_llm=request.use_mock_llm,
            required_resources_per_topic=0,
        )
        return await self.review_curriculum_with_resources(critic_request)

    async def review_curriculum_with_resources(
        self,
        request: CriticReviewRequest,
    ) -> CriticReviewResult:
        if request.use_mock_llm:
            result = await review_with_mock_llm(request)
        else:
            result = review_with_deterministic_rubric(request)
        self.store.save(result)
        return result

    def get_latest_review(self, curriculum_id: str) -> CriticReviewResult | None:
        return self.store.latest(curriculum_id)

    def list_reviews_for_curriculum(self, curriculum_id: str) -> list[CriticReviewResult]:
        return self.store.list_for_curriculum(curriculum_id)

    def get_critic_rubric_summary(self) -> CriticRubricSummary:
        return get_rubric_summary()

    def to_graph_critic_review(self, result: CriticReviewResult) -> GraphCriticReview:
        decision: CriticDecision
        if result.auto_approved:
            decision = "auto_approved"
        elif result.approved:
            decision = "approved"
        else:
            decision = "revise"
        return GraphCriticReview(
            decision=decision,
            approved=result.approved,
            score=result.overall_quality_score,
            auto_approved=result.auto_approved,
            revision_instructions=_revision_text(result),
        )


def _revision_text(result: CriticReviewResult) -> str | None:
    if result.approved and not result.auto_approved:
        return None
    if not result.revision_instructions:
        return None
    return " ".join(instruction.instruction for instruction in result.revision_instructions[:3])
