from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.agents.deterministic.quiz import LOW_SCORE_THRESHOLD
from app.agents.services.adaptation import AdaptationAgentService
from app.agents.services.progress import ProgressAgentService
from app.agents.services.quiz import QuizAgentService
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAnswerSubmission, QuizAttemptDTO, QuizDTO
from app.services import CurriculumService, GoalService


@dataclass(slots=True)
class QuizSubmissionResult:
    attempt: QuizAttemptDTO
    progress: ProgressStateDTO
    adaptation_event: AdaptationEventDTO | None


@dataclass(slots=True)
class QuizSubmissionService:
    """Composes the real post-submission flow a genuine learner quiz attempt
    triggers (Big_Audit Step 11): score the attempt (Step 10), recompute real
    Progress from it, then explicitly decide whether a real Adaptation event
    is actually warranted before ever calling `AdaptationAgentService.plan()`.

    `plan()` has no "should we adapt" logic of its own - `_trigger_type()`
    always resolves to *some* trigger type once called (its final branch
    unconditionally returns `QUIZ_SCORE_BELOW_THRESHOLD` even when neither
    real condition holds). The gate must live in the caller, not inside
    `plan()` and not in the API route (RULES.md SS3/SS4 - no business logic
    in routes), so it lives here: a dedicated composition point rather than
    folding it into `QuizAgentService` (stays scoped to quizzes only,
    RULES.md SS11) or into `ProgressAgentService`/`AdaptationAgentService`
    (stay scoped to their own domains - both are still exactly what the demo
    orchestration graph uses, unchanged).
    """

    quiz_agent: QuizAgentService
    progress_agent: ProgressAgentService
    adaptation_agent: AdaptationAgentService
    goals: GoalService
    curricula: CurriculumService

    def submit(
        self,
        quiz: QuizDTO,
        answers: list[QuizAnswerSubmission],
    ) -> QuizSubmissionResult:
        attempt = self.quiz_agent.submit_attempt(quiz, answers)
        goal = self.goals.get_by_id(quiz.goal_id)
        curriculum = self.curricula.get_by_id(quiz.curriculum_id)

        existing_progress = self.progress_agent.progress.list_by_goal_id(goal.goal_id)
        progress_state_id = (
            existing_progress[0].progress_state_id
            if existing_progress
            else _new_id("progress")
        )
        progress_state = self.progress_agent.build(
            goal,
            curriculum,
            attempt,
            progress_state_id=progress_state_id,
        )

        adaptation_event = self._maybe_trigger_adaptation(
            goal=goal,
            curriculum=curriculum,
            progress_state=progress_state,
            attempt=attempt,
        )
        return QuizSubmissionResult(
            attempt=attempt,
            progress=progress_state,
            adaptation_event=adaptation_event,
        )

    def _maybe_trigger_adaptation(
        self,
        *,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        progress_state: ProgressStateDTO,
        attempt: QuizAttemptDTO,
    ) -> AdaptationEventDTO | None:
        # The non-negotiable gate (Big_Audit Step 11): plan() itself has no
        # real "should we adapt" logic, so a genuine trigger condition must
        # be confirmed here, explicitly, before it is ever called for a real
        # learner. A healthy submission (good score, no stuck topics) must
        # create zero adaptation events.
        should_trigger = (
            attempt.total_score < LOW_SCORE_THRESHOLD or bool(progress_state.stuck_events)
        )
        if not should_trigger:
            return None

        existing_adaptations = self.adaptation_agent.adaptations.list_by_goal_id(goal.goal_id)
        adaptation_event_id = (
            existing_adaptations[0].adaptation_event_id
            if existing_adaptations
            else _new_id("adapt")
        )
        return self.adaptation_agent.plan(
            goal,
            curriculum,
            progress_state,
            attempt,
            adaptation_event_id=adaptation_event_id,
        )


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
