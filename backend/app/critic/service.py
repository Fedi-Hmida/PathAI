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


class CriticService:
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
            return await review_with_mock_llm(request)
        return review_with_deterministic_rubric(request)

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
