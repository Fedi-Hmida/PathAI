from __future__ import annotations

from dataclasses import dataclass

from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import EvaluationPassStatus, OrchestrationStatus
from app.schemas.ids import RunId
from app.schemas.reporting import ReportingSummaryDTO
from app.services.dashboard import DashboardService


@dataclass(slots=True)
class ReportingService:
    dashboard: DashboardService

    def get_summary_by_run_id(self, run_id: RunId) -> ReportingSummaryDTO:
        payload = self.dashboard.get_by_run_id(run_id)
        return ReportingSummaryDTO(
            run_id=payload.run_summary.run_id,
            goal_id=payload.goal_summary.goal_id,
            status=payload.run_summary.status,
            deterministic=payload.run_summary.mode.value == "demo",
            demo_ready=_demo_ready(payload),
            artifact_ids=payload.navigation_summary.artifact_ids,
            overall_quality_score=(
                payload.evaluation_summary.overall_score
                if payload.evaluation_summary
                else None
            ),
            evaluation_pass_status=(
                payload.evaluation_summary.pass_status
                if payload.evaluation_summary
                else None
            ),
            weak_concepts=_weak_concepts(payload),
            current_topic=(
                payload.progress_summary.current_topic
                if payload.progress_summary
                else None
            ),
            next_action=_next_action(payload),
            critic_warnings=_critic_warnings(payload),
            adaptation_warnings=_adaptation_warnings(payload),
            readiness_notes=_readiness_notes(payload),
        )


def _demo_ready(payload: DashboardPayload) -> bool:
    return (
        payload.run_summary.status == OrchestrationStatus.COMPLETED
        and payload.evaluation_summary is not None
        and payload.evaluation_summary.pass_status
        in {EvaluationPassStatus.PASS, EvaluationPassStatus.PASS_WITH_WARNINGS}
        and payload.progress_summary is not None
        and payload.quiz_summary is not None
    )


def _weak_concepts(payload: DashboardPayload) -> list[str]:
    values: list[str] = []
    if payload.knowledge_map_summary:
        values.extend(payload.knowledge_map_summary.weak_concepts)
    if payload.progress_summary:
        values.extend(payload.progress_summary.weak_concepts)
    if payload.quiz_summary:
        values.extend(payload.quiz_summary.weak_concepts)
    return _unique(values)


def _next_action(payload: DashboardPayload) -> str | None:
    if payload.progress_summary is None:
        return None
    if (
        payload.progress_summary.next_action_label
        and payload.progress_summary.next_action_reason
    ):
        return (
            f"{payload.progress_summary.next_action_label}: "
            f"{payload.progress_summary.next_action_reason}"
        )
    return payload.progress_summary.next_action_label


def _critic_warnings(payload: DashboardPayload) -> list[str]:
    if payload.critic_summary is None:
        return []
    return payload.critic_summary.top_issues[:10]


def _adaptation_warnings(payload: DashboardPayload) -> list[str]:
    if payload.adaptation_summary is None:
        return []
    warnings = payload.adaptation_summary.recent_events[:5]
    if payload.adaptation_summary.latest_status:
        warnings.append(f"latest_status={payload.adaptation_summary.latest_status.value}")
    return warnings[:10]


def _readiness_notes(payload: DashboardPayload) -> list[str]:
    notes: list[str] = []
    if payload.evaluation_summary is None:
        notes.append("Evaluation report is missing.")
    if (
        payload.resources_summary
        and payload.resources_summary.resource_type_diversity is not None
    ):
        notes.append(
            f"Resource diversity score: {payload.resources_summary.resource_type_diversity:.2f}.",
        )
    if payload.quiz_summary and payload.quiz_summary.latest_score is not None:
        notes.append(f"Latest quiz score: {payload.quiz_summary.latest_score:.2f}.")
    if payload.adaptation_summary and payload.adaptation_summary.recent_events:
        notes.append("Adaptation suggestion is visible in the dashboard summary.")
    return notes[:10]


def _unique(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values
