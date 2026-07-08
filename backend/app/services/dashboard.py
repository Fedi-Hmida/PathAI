from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from app.repositories.errors import NotFoundError
from app.repositories.protocols.adaptation import AdaptationRepository
from app.repositories.protocols.assessment import AssessmentRepository
from app.repositories.protocols.critic import CriticReviewRepository
from app.repositories.protocols.curriculum import CurriculumRepository
from app.repositories.protocols.evaluation import EvaluationRepository
from app.repositories.protocols.goal import GoalRepository
from app.repositories.protocols.knowledge_map import KnowledgeMapRepository
from app.repositories.protocols.orchestration import OrchestrationRunRepository
from app.repositories.protocols.progress import ProgressRepository
from app.repositories.protocols.quiz import QuizRepository
from app.repositories.protocols.resource import ResourceRepository
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.dashboard import (
    AdaptationSummary,
    AssessmentSummary,
    CriticSummary,
    CurriculumSummary,
    CurriculumWeekSummary,
    DashboardPayload,
    DashboardUIFlags,
    EvaluationSummary,
    GoalSummary,
    KnowledgeMapSummary,
    NavigationSummary,
    ProgressSummary,
    QuizSummary,
    ResourcesSummary,
    RunSummary,
)
from app.schemas.enums import ExecutionMode, OrchestrationRunStatus, OrchestrationStatus
from app.schemas.ids import RunId, TopicId
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.resource import ResourceAttachmentDTO

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
    assessments: AssessmentRepository | None = None
    critics: CriticReviewRepository | None = None

    def get_by_run_id(self, run_id: RunId) -> DashboardPayload:
        run = self.orchestration_runs.get_by_id(run_id)
        goal = self.goals.get_by_run_id(run_id)
        knowledge_map = _last_or_none(self.knowledge_maps.list_by_run_id(run_id))
        curriculum = _last_or_none(self.curricula.list_by_run_id(run_id))
        assessment = _assessment_for_knowledge_map(self.assessments, knowledge_map)
        progress = _last_or_none(self.progress_states.list_by_goal_id(goal.goal_id))
        attachments = self.resources.list_attachments_by_goal_id(goal.goal_id)
        attempts = self.quizzes.list_attempts_by_goal_id(goal.goal_id)
        adaptations = self.adaptations.list_by_goal_id(goal.goal_id)
        critic = (
            _last_or_none(self.critics.list_by_curriculum_id(curriculum.curriculum_id))
            if self.critics is not None and curriculum is not None
            else None
        )
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
            round(
                sum(attachment.relevance_score for attachment in attachments)
                / len(attachments),
                2,
            )
            if attachments
            else None
        )
        latest_adaptation = adaptations[-1] if adaptations else None

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
            navigation_summary=NavigationSummary(
                artifact_ids=_artifact_ids(
                    run_id=run_id,
                    goal_id=goal.goal_id,
                    assessment_id=assessment.assessment_session_id if assessment else None,
                    knowledge_map_id=knowledge_map.knowledge_map_id
                    if knowledge_map
                    else None,
                    curriculum_id=curriculum.curriculum_id if curriculum else None,
                    progress_state_id=progress.progress_state_id if progress else None,
                    quiz_id=latest_attempt.quiz_id if latest_attempt else None,
                    quiz_attempt_id=latest_attempt.quiz_attempt_id
                    if latest_attempt
                    else None,
                    adaptation_event_id=latest_adaptation.adaptation_event_id
                    if latest_adaptation
                    else None,
                    critic_review_id=critic.critic_review_id if critic else None,
                    evaluation_report_id=evaluation.evaluation_report_id
                    if evaluation
                    else None,
                ),
            ),
            assessment_summary=(
                AssessmentSummary(
                    assessment_session_id=assessment.assessment_session_id,
                    status=assessment.status,
                    question_count=assessment.question_count,
                    confidence=assessment.confidence,
                    termination_reason=assessment.termination_reason,
                )
                if assessment is not None
                else None
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
                    next_action_label=progress.next_recommended_action.label
                    if progress.next_recommended_action
                    else None,
                    next_action_reason=progress.next_recommended_action.reason
                    if progress.next_recommended_action
                    else None,
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
                resource_type_diversity=_resource_type_diversity(attachments),
            ),
            adaptation_summary=AdaptationSummary(
                recent_events=[event.after_summary for event in adaptations[-10:]],
                latest_status=latest_adaptation.status if latest_adaptation else None,
            ),
            critic_summary=(
                CriticSummary(
                    overall_score=critic.overall_score,
                    pass_status=critic.pass_status,
                    issue_count=len(critic.issues),
                    top_issues=critic.issues[:5],
                )
                if critic is not None
                else None
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


def _assessment_for_knowledge_map(
    repository: AssessmentRepository | None,
    knowledge_map: KnowledgeMapDTO | None,
) -> AssessmentSessionDTO | None:
    if repository is None or knowledge_map is None:
        return None
    try:
        return repository.get_session_by_id(knowledge_map.assessment_session_id)
    except NotFoundError:
        return None


def _resource_type_diversity(
    attachments: list[ResourceAttachmentDTO],
) -> float | None:
    if not attachments:
        return None
    categories = {
        attachment.diversity_category
        for attachment in attachments
        if attachment.diversity_category
    }
    return round(min(1.0, len(categories) / 5), 2)


def _artifact_ids(
    *,
    run_id: str,
    goal_id: str,
    assessment_id: str | None,
    knowledge_map_id: str | None,
    curriculum_id: str | None,
    progress_state_id: str | None,
    quiz_id: str | None,
    quiz_attempt_id: str | None,
    adaptation_event_id: str | None,
    critic_review_id: str | None,
    evaluation_report_id: str | None,
) -> dict[str, str]:
    candidates = {
        "run_id": run_id,
        "goal_id": goal_id,
        "assessment_id": assessment_id,
        "knowledge_map_id": knowledge_map_id,
        "curriculum_id": curriculum_id,
        "progress_state_id": progress_state_id,
        "quiz_id": quiz_id,
        "quiz_attempt_id": quiz_attempt_id,
        "adaptation_event_id": adaptation_event_id,
        "critic_review_id": critic_review_id,
        "evaluation_report_id": evaluation_report_id,
    }
    return {
        key: value
        for key, value in candidates.items()
        if value is not None
    }


def require_dashboard_payload(payload: DashboardPayload | None) -> DashboardPayload:
    if payload is None:
        msg = "dashboard payload not found"
        raise NotFoundError(msg)
    return payload
