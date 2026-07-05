from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from app.repositories.errors import NotFoundError
from app.repositories.protocols.adaptation import AdaptationRepository
from app.repositories.protocols.curriculum import CurriculumRepository
from app.repositories.protocols.evaluation import EvaluationRepository
from app.repositories.protocols.goal import GoalRepository
from app.repositories.protocols.knowledge_map import KnowledgeMapRepository
from app.repositories.protocols.orchestration import OrchestrationRunRepository
from app.repositories.protocols.progress import ProgressRepository
from app.repositories.protocols.quiz import QuizRepository
from app.repositories.protocols.resource import ResourceRepository
from app.schemas.curriculum import CurriculumDTO
from app.schemas.dashboard import (
    AdaptationSummary,
    CurriculumSummary,
    CurriculumWeekSummary,
    DashboardPayload,
    DashboardUIFlags,
    EvaluationSummary,
    GoalSummary,
    KnowledgeMapSummary,
    ProgressSummary,
    QuizSummary,
    ResourcesSummary,
    RunSummary,
)
from app.schemas.enums import ExecutionMode, OrchestrationRunStatus, OrchestrationStatus
from app.schemas.ids import RunId, TopicId

ItemT = TypeVar("ItemT")

RUN_STATUS_MAP: dict[OrchestrationRunStatus, OrchestrationStatus] = {
    OrchestrationRunStatus.CREATED: OrchestrationStatus.QUEUED,
    OrchestrationRunStatus.IN_PROGRESS: OrchestrationStatus.RUNNING,
    OrchestrationRunStatus.REQUIRES_INPUT: OrchestrationStatus.WAITING_FOR_USER,
    OrchestrationRunStatus.COMPLETED: OrchestrationStatus.COMPLETED,
    OrchestrationRunStatus.COMPLETED_WITH_WARNINGS: OrchestrationStatus.COMPLETED,
    OrchestrationRunStatus.FAILED: OrchestrationStatus.FAILED,
}


@dataclass(slots=True)
class DashboardService:
    goals: GoalRepository
    orchestration_runs: OrchestrationRunRepository
    knowledge_maps: KnowledgeMapRepository
    curricula: CurriculumRepository
    resources: ResourceRepository
    progress_states: ProgressRepository
    quizzes: QuizRepository
    adaptations: AdaptationRepository
    evaluations: EvaluationRepository

    def get_by_run_id(self, run_id: RunId) -> DashboardPayload:
        run = self.orchestration_runs.get_by_id(run_id)
        goal = self.goals.get_by_run_id(run_id)
        knowledge_map = _last_or_none(self.knowledge_maps.list_by_run_id(run_id))
        curriculum = _last_or_none(self.curricula.list_by_run_id(run_id))
        progress = _last_or_none(self.progress_states.list_by_goal_id(goal.goal_id))
        attachments = self.resources.list_attachments_by_goal_id(goal.goal_id)
        attempts = self.quizzes.list_attempts_by_goal_id(goal.goal_id)
        adaptations = self.adaptations.list_by_goal_id(goal.goal_id)
        evaluation = _last_or_none(self.evaluations.list_by_run_id(run_id))

        current_topic = None
        if (
            curriculum is not None
            and progress is not None
            and progress.current_topic_id is not None
        ):
            current_topic = _topic_title(curriculum, progress.current_topic_id)

        latest_attempt = (
            max(attempts, key=lambda attempt: attempt.submitted_at)
            if attempts
            else None
        )
        average_relevance = (
            sum(attachment.relevance_score for attachment in attachments) / len(attachments)
            if attachments
            else None
        )

        return DashboardPayload(
            run_summary=RunSummary(
                run_id=run.run_id,
                status=RUN_STATUS_MAP[run.status],
                mode=ExecutionMode.DEMO if goal.demo_seed_id else ExecutionMode.INTERACTIVE,
                current_node=run.current_node,
            ),
            goal_summary=GoalSummary(
                goal_id=goal.goal_id,
                text=goal.goal_text,
                status=goal.status,
            ),
            knowledge_map_summary=(
                KnowledgeMapSummary(
                    strong_concepts=knowledge_map.strong_concepts,
                    weak_concepts=knowledge_map.weak_concepts,
                    summary=knowledge_map.summary,
                )
                if knowledge_map is not None
                else None
            ),
            curriculum_summary=(
                CurriculumSummary(
                    active_curriculum_id=curriculum.curriculum_id,
                    title=curriculum.title,
                    weeks=[
                        CurriculumWeekSummary(
                            week_number=week.week_number,
                            theme=week.theme,
                            topic_titles=[topic.title for topic in week.topics],
                        )
                        for week in curriculum.weeks
                    ],
                )
                if curriculum is not None
                else None
            ),
            progress_summary=(
                ProgressSummary(
                    completion_percentage=round(progress.overall_completion * 100),
                    current_topic=current_topic,
                    weak_concepts=progress.weak_concepts,
                )
                if progress is not None
                else None
            ),
            quiz_summary=(
                QuizSummary(
                    latest_score=latest_attempt.total_score,
                    weak_concepts=latest_attempt.weak_concepts,
                )
                if latest_attempt is not None
                else None
            ),
            resources_summary=ResourcesSummary(
                total_attached=len(attachments),
                average_relevance=average_relevance,
            ),
            adaptation_summary=AdaptationSummary(
                recent_events=[event.after_summary for event in adaptations[-10:]],
            ),
            evaluation_summary=(
                EvaluationSummary(
                    overall_score=evaluation.overall_score,
                    pass_status=evaluation.pass_status,
                )
                if evaluation is not None
                else None
            ),
            ui_flags=DashboardUIFlags(
                show_adaptation_alert=bool(adaptations),
                requires_user_input=run.status == OrchestrationRunStatus.REQUIRES_INPUT,
            ),
        )


def _last_or_none(items: list[ItemT]) -> ItemT | None:
    if not items:
        return None
    return items[-1]


def _topic_title(curriculum: CurriculumDTO, topic_id: TopicId) -> str | None:
    for week in curriculum.weeks:
        for topic in week.topics:
            if topic.topic_id == topic_id:
                return topic.title
    return None


def require_dashboard_payload(payload: DashboardPayload | None) -> DashboardPayload:
    if payload is None:
        msg = "dashboard payload not found"
        raise NotFoundError(msg)
    return payload
