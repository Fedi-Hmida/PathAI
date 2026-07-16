from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import CurriculumAgent
from app.agents.services.common import create_or_get, create_or_replace, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput, CurriculumDTO
from app.schemas.enums import CurriculumStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.services import CurriculumService


@dataclass(slots=True)
class CurriculumAgentService:
    agent: CurriculumAgent
    curricula: CurriculumService

    def build(
        self,
        goal: LearningGoalDTO,
        knowledge_map: KnowledgeMapDTO,
        *,
        critic_recommendations: list[str] | None = None,
        revision_attempt: int = 0,
        curriculum_id: str | None = None,
    ) -> CurriculumDTO:
        recommendations = list(critic_recommendations or [])[:10]
        payload = CurriculumAgentInput(
            goal_text=goal.goal_text,
            learner_profile=goal.learner_profile,
            knowledge_map=knowledge_map,
            duration_weeks=goal.target_duration_weeks or demo.CURRICULUM.duration_weeks,
            # goal.hours_per_week is an optional override; a workspace's goal
            # never sets it (see workspace_factory.py), so fall back to the
            # learner profile's own time-availability figure, which every
            # goal always has.
            hours_per_week=(
                goal.hours_per_week or goal.learner_profile.time_availability_hours_per_week
            ),
            critic_recommendations=recommendations,
        )
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=CurriculumAgentOutput,
            payload=self.agent.build_curriculum(payload),
        )
        curriculum = CurriculumDTO(
            curriculum_id=curriculum_id or demo.CURRICULUM_ID,
            goal_id=goal.goal_id,
            knowledge_map_id=knowledge_map.knowledge_map_id,
            run_id=goal.run_id,
            status=CurriculumStatus.ACTIVE,
            title=output.title,
            duration_weeks=output.duration_weeks,
            weeks=output.weeks,
            target_outcomes=output.target_outcomes,
            assumptions=output.assumptions,
            critic_revision_attempt=revision_attempt,
            revision_reason="critic-driven revision" if revision_attempt > 0 else None,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        # A revision always targets an already-created curriculum (its own
        # first pass created it), so this overwrites in place rather than
        # relying on create-or-get's first-write-wins idempotency, which only
        # fits the single demo pipeline's first pass.
        if revision_attempt > 0:
            return self.curricula.save(curriculum)
        # An explicit per-user curriculum_id (from workspace generation):
        # create it fresh the first time, or overwrite in place on a repeat
        # call.
        if curriculum_id is not None:
            return create_or_replace(
                create=self.curricula.create,
                save=self.curricula.save,
                record=curriculum,
            )
        return create_or_get(
            create=self.curricula.create,
            get=self.curricula.get_by_id,
            record=curriculum,
            record_id=curriculum.curriculum_id,
        )
