from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import CriticAgent
from app.agents.services.common import create_or_get, create_or_replace, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput, CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.resource import ResourceAttachmentDTO
from app.services import CriticService


@dataclass(slots=True)
class CriticAgentService:
    agent: CriticAgent
    critics: CriticService

    def review(
        self,
        goal: LearningGoalDTO,
        knowledge_map: KnowledgeMapDTO,
        curriculum: CurriculumDTO,
        attachments: list[ResourceAttachmentDTO],
        *,
        revision_attempt: int = 0,
        critic_review_id: str | None = None,
    ) -> CriticReviewDTO:
        payload = CriticAgentInput(
            goal_text=goal.goal_text,
            knowledge_map=knowledge_map,
            curriculum=curriculum,
            resource_attachments=attachments,
            rubric_weights={},
        )
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=CriticAgentOutput,
            payload=self.agent.review_curriculum(payload),
        )
        review = CriticReviewDTO(
            critic_review_id=critic_review_id or demo.CRITIC_REVIEW_ID,
            goal_id=goal.goal_id,
            curriculum_id=curriculum.curriculum_id,
            run_id=goal.run_id,
            overall_score=output.overall_score,
            pass_status=output.pass_status,
            dimension_scores=output.dimension_scores,
            strengths=output.strengths,
            issues=output.issues,
            revision_recommendations=output.revision_recommendations,
            revision_attempt=revision_attempt,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        # On a revision, re-review the regenerated curriculum by overwriting the
        # prior review in place rather than returning the stale create-or-get hit.
        if revision_attempt > 0:
            return self.critics.save(review)
        # An explicit per-user critic_review_id (from workspace generation):
        # create it fresh the first time, or overwrite in place on a repeat
        # call.
        if critic_review_id is not None:
            return create_or_replace(
                create=self.critics.create,
                save=self.critics.save,
                record=review,
            )
        return create_or_get(
            create=self.critics.create,
            get=self.critics.get_by_id,
            record=review,
            record_id=review.critic_review_id,
        )
