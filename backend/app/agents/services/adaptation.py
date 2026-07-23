from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import AdapterAgent
from app.agents.deterministic.quiz import LOW_SCORE_THRESHOLD
from app.agents.mock import MockAdapterAgent
from app.agents.services.common import create_or_get, create_or_replace, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.adaptation import (
    AdaptationAgentInput,
    AdaptationAgentOutput,
    AdaptationEventDTO,
)
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import AdaptationStatus, AdaptationTriggerType
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
        *,
        adaptation_event_id: str | None = None,
    ) -> AdaptationEventDTO:
        resolved_id = adaptation_event_id or demo.ADAPTATION_ID
        payload = AdaptationAgentInput(
            goal_text=goal.goal_text,
            curriculum=curriculum,
            progress_state=progress_state,
            quiz_attempt=quiz_attempt,
            weak_concepts=progress_state.weak_concepts,
            stuck_events=progress_state.stuck_events,
            adaptation_event_id=resolved_id,
        )
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=AdaptationAgentOutput,
            payload=self.agent.plan_adaptation(payload),
        )
        event = AdaptationEventDTO(
            adaptation_event_id=resolved_id,
            goal_id=goal.goal_id,
            curriculum_id=curriculum.curriculum_id,
            trigger_type=_trigger_type(progress_state, quiz_attempt),
            trigger_details=_trigger_details(output, progress_state, quiz_attempt),
            before_summary=output.before_summary,
            after_summary=output.after_summary,
            changes=output.changes,
            status=AdaptationStatus.PROPOSED,
            quiz_attempt_id=quiz_attempt.quiz_attempt_id if quiz_attempt else None,
            stuck_event_ids=[
                f"{stuck_event.topic_id}:stuck"
                for stuck_event in progress_state.stuck_events
            ],
            new_curriculum_id=None,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        # An explicit ID means a real per-user trigger (first-time or
        # re-trigger): create it fresh the first time, or overwrite in place
        # on a repeat call - mirrors ProgressAgentService.build()'s identical
        # fix in Step 9. No explicit ID means the single fixed-ID demo
        # pipeline, unchanged first-write-wins behavior.
        if adaptation_event_id is not None:
            return create_or_replace(
                create=self.adaptations.create,
                save=self.adaptations.save,
                record=event,
            )
        return create_or_get(
            create=self.adaptations.create,
            get=self.adaptations.get_by_id,
            record=event,
            record_id=event.adaptation_event_id,
        )


def _trigger_type(
    progress_state: ProgressStateDTO,
    quiz_attempt: QuizAttemptDTO | None,
) -> AdaptationTriggerType:
    if quiz_attempt and quiz_attempt.total_score < LOW_SCORE_THRESHOLD:
        return AdaptationTriggerType.QUIZ_SCORE_BELOW_THRESHOLD
    if progress_state.stuck_events:
        return AdaptationTriggerType.STUCK_EVENT_THRESHOLD
    return AdaptationTriggerType.QUIZ_SCORE_BELOW_THRESHOLD


def _trigger_details(
    output: AdaptationAgentOutput,
    progress_state: ProgressStateDTO,
    quiz_attempt: QuizAttemptDTO | None,
) -> dict[str, str]:
    details = {
        "reason": output.trigger_reason,
        "threshold": f"{LOW_SCORE_THRESHOLD:.2f}",
    }
    if quiz_attempt:
        details["quiz_score"] = f"{quiz_attempt.total_score:.2f}"
        details["quiz_attempt_id"] = quiz_attempt.quiz_attempt_id
    if progress_state.current_topic_id:
        details["current_topic_id"] = progress_state.current_topic_id
    if progress_state.stuck_events:
        details["stuck_event_count"] = str(len(progress_state.stuck_events))
    return details


def build_default_adaptation_agent_service(
    adaptations: AdaptationService,
) -> AdaptationAgentService:
    """The adaptation agent has no LLM mode - it is always this
    deterministic default. Exists so `app/orchestration/*_gateway.py` modules
    never have to reference `app.agents.mock` directly - forbidden there by
    `test_agent_scope_security.py`, the same way `bundle.py` and
    `app/agents/services/quiz.py`'s `build_default_quiz_agent_service` keep
    that reference confined to `app/agents/services/`."""
    return AdaptationAgentService(MockAdapterAgent(), adaptations)
