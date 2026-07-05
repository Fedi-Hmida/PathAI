from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import AdapterAgent
from app.agents.services.common import create_or_get, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.adaptation import (
    AdaptationAgentInput,
    AdaptationAgentOutput,
    AdaptationEventDTO,
)
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import AdaptationStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAttemptDTO
from app.services import AdaptationService


@dataclass(slots=True)
class AdaptationAgentService:
    agent: AdapterAgent
    adaptations: AdaptationService

    def plan(
        self,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        progress_state: ProgressStateDTO,
        quiz_attempt: QuizAttemptDTO | None,
    ) -> AdaptationEventDTO:
        payload = AdaptationAgentInput(
            goal_text=goal.goal_text,
            curriculum=curriculum,
            progress_state=progress_state,
            quiz_attempt=quiz_attempt,
            weak_concepts=progress_state.weak_concepts,
            stuck_events=progress_state.stuck_events,
        )
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=AdaptationAgentOutput,
            payload=self.agent.plan_adaptation(payload),
        )
        event = AdaptationEventDTO(
            adaptation_event_id=demo.ADAPTATION_ID,
            goal_id=goal.goal_id,
            curriculum_id=curriculum.curriculum_id,
            trigger_type=demo.ADAPTATION_EVENT.trigger_type,
            trigger_details=demo.ADAPTATION_EVENT.trigger_details,
            before_summary=output.before_summary,
            after_summary=output.after_summary,
            changes=output.changes,
            status=AdaptationStatus.APPLIED,
            quiz_attempt_id=quiz_attempt.quiz_attempt_id if quiz_attempt else None,
            new_curriculum_id=demo.ADAPTATION_EVENT.new_curriculum_id,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        return create_or_get(
            create=self.adaptations.create,
            get=self.adaptations.get_by_id,
            record=event,
            record_id=event.adaptation_event_id,
        )
