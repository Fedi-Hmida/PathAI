from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.agents.errors import AgentError
from app.agents.services import AgentServiceBundle, build_mock_agent_service_bundle
from app.agents.services.activation import build_injected_agents, resolve_agent_integration_switches
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.orchestration.events import (
    node_completed_event,
    node_failed_event,
    safe_agent_workflow_error,
    safe_workflow_error,
)
from app.orchestration.state import GraphState, increment_node_attempt, merge_state
from app.repositories.errors import DuplicateRecordError, NotFoundError
from app.schemas.base import WorkflowWarning
from app.schemas.enums import CriticPassStatus, OrchestrationRunStatus, OrchestrationStatus
from app.schemas.orchestration import OrchestrationRunDTO
from app.services import (
    AdaptationService,
    AssessmentService,
    CriticService,
    CurriculumService,
    DashboardService,
    EvaluationService,
    GoalService,
    KnowledgeMapService,
    OrchestrationRunService,
    ProgressService,
    QuizService,
    ReportingService,
    ResourceService,
)

NODE_SEQUENCE: tuple[str, ...] = (
    "initialize_run",
    "load_goal",
    "load_assessment",
    "load_knowledge_map",
    "load_curriculum",
    "load_resources",
    "load_critic_review",
    "load_progress",
    "load_quiz",
    "load_adaptation",
    "load_evaluation",
    "prepare_dashboard_payload",
    "complete_run",
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class ServiceContainerProtocol(Protocol):
    goal_service: GoalService
    assessment_service: AssessmentService
    knowledge_map_service: KnowledgeMapService
    curriculum_service: CurriculumService
    resource_service: ResourceService
    progress_service: ProgressService
    quiz_service: QuizService
    adaptation_service: AdaptationService
    critic_service: CriticService
    evaluation_service: EvaluationService
    orchestration_run_service: OrchestrationRunService
    dashboard_service: DashboardService
    reporting_service: ReportingService


@dataclass(slots=True)
class OrchestrationContext:
    goals: GoalService
    assessments: AssessmentService
    knowledge_maps: KnowledgeMapService
    curricula: CurriculumService
    resources: ResourceService
    progress: ProgressService
    quizzes: QuizService
    adaptations: AdaptationService
    critics: CriticService
    evaluations: EvaluationService
    orchestration_runs: OrchestrationRunService
    dashboard: DashboardService
    reporting: ReportingService
    agent_services: AgentServiceBundle

    @classmethod
    def from_container(
        cls,
        container: ServiceContainerProtocol,
        agent_services: AgentServiceBundle | None = None,
    ) -> OrchestrationContext:
        agents = agent_services or _build_default_agent_service_bundle(container)
        return cls(
            goals=container.goal_service,
            assessments=container.assessment_service,
            knowledge_maps=container.knowledge_map_service,
            curricula=container.curriculum_service,
            resources=container.resource_service,
            progress=container.progress_service,
            quizzes=container.quiz_service,
            adaptations=container.adaptation_service,
            critics=container.critic_service,
            evaluations=container.evaluation_service,
            orchestration_runs=container.orchestration_run_service,
            dashboard=container.dashboard_service,
            reporting=container.reporting_service,
            agent_services=agents,
        )


def _build_default_agent_service_bundle(
    container: ServiceContainerProtocol,
) -> AgentServiceBundle:
    """Build the agent bundle a caller gets when it doesn't inject one explicitly.

    Resolves LLM activation from `Settings` (via the Rebuild-14B/14C activation
    package) so an operator-set `PATHAI_ENABLE_LLM_*_AGENT` flag actually takes
    effect on this default path. With no flags set, `resolve_agent_integration_switches`
    returns the same all-deterministic `AgentIntegrationSwitches()` this bundle
    was built with before this function existed — this default path is a no-op
    unless an operator has explicitly opted in.

    All four agents (knowledge_map: Rebuild-14D, assessment: Rebuild-14F,
    critic/curriculum: Rebuild-14G) are now verified end-to-end through this
    orchestration path. The one-agent-at-a-time invariant is enforced solely by
    `resolve_agent_integration_switches`, which raises `ActivationConfigError`
    if 2+ flags are set — no additional guard is needed here now that every
    switch has a real, wired destination.
    """
    settings = get_settings()
    switches = resolve_agent_integration_switches(settings)
    injected = build_injected_agents(switches, settings)
    return build_mock_agent_service_bundle(
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
        switches=switches,
        assessment_agent=injected.assessment,
        knowledge_map_agent=injected.knowledge_map,
        critic_agent=injected.critic,
        curriculum_agent=injected.curriculum,
    )


NodeBody = Callable[[GraphState, OrchestrationContext], GraphState]


def run_node(
    node_name: str,
    state: GraphState,
    context: OrchestrationContext,
    body: NodeBody,
) -> GraphState:
    attempted_state = increment_node_attempt(state, node_name)
    try:
        next_state = body(attempted_state, context)
    except AgentError as exc:
        return _mark_node_failed(attempted_state, context, node_name, exc)
    except Exception:
        return _mark_node_failed(attempted_state, context, node_name)
    return _mark_node_completed(next_state, context, node_name)


def initialize_run(state: GraphState, context: OrchestrationContext) -> GraphState:
    run_id = state["run_id"]
    goal_id = state.get("goal_id")
    now = _now()
    run = OrchestrationRunDTO(
        run_id=run_id,
        goal_id=goal_id,
        workflow_version="demo-v1",
        status=OrchestrationRunStatus.IN_PROGRESS,
        current_node="initialize_run",
        completed_nodes=[],
        failed_nodes=[],
        node_events=[],
        artifact_ids=_artifact_ids(state),
        started_at=now,
        created_at=now,
        updated_at=now,
    )
    try:
        context.orchestration_runs.create(run)
    except DuplicateRecordError:
        existing = context.orchestration_runs.get_by_id(run_id)
        context.orchestration_runs.save(
            existing.model_copy(
                update={
                    "status": OrchestrationRunStatus.IN_PROGRESS,
                    "current_node": "initialize_run",
                    "updated_at": now,
                },
                deep=True,
            ),
        )
    return merge_state(
        state,
        status=OrchestrationStatus.RUNNING,
        current_node="initialize_run",
    )


def load_goal(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _create_or_get(
        create=context.goals.create,
        get=context.goals.get_by_id,
        record=demo.LEARNING_GOAL,
        record_id=demo.GOAL_ID,
    )
    return merge_state(state, goal_id=goal.goal_id)


def load_assessment(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    session = context.agent_services.assessment.run_diagnostic(goal)
    return merge_state(
        state,
        assessment_session_id=session.assessment_session_id,
        assessment_question_count=session.question_count,
        assessment_confidence=session.confidence,
    )


def load_knowledge_map(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    session = context.assessments.get_session_by_id(
        state.get("assessment_session_id") or demo.ASSESSMENT_ID,
    )
    answers = context.assessments.list_answers_by_session_id(session.assessment_session_id)
    knowledge_map = context.agent_services.knowledge_map.build(goal, session, answers)
    return merge_state(state, knowledge_map_id=knowledge_map.knowledge_map_id)


def load_curriculum(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    knowledge_map = context.knowledge_maps.get_by_id(
        state.get("knowledge_map_id") or demo.KNOWLEDGE_MAP_ID,
    )
    # The wrapper increments node_attempts before this body runs, so the Nth visit
    # to load_curriculum is revision N-1. Deriving the count from visits (not from
    # whether recommendations happen to be non-empty) makes the loop terminate even
    # when the critic asks to revise without naming specific recommendations.
    revision_attempt = max(0, state.get("node_attempts", {}).get("load_curriculum", 1) - 1)
    curriculum = context.agent_services.curriculum.build(
        goal,
        knowledge_map,
        critic_recommendations=state.get("critic_recommendations", []),
        revision_attempt=revision_attempt,
    )
    return merge_state(
        state,
        curriculum_id=curriculum.curriculum_id,
        critic_revision_attempts=revision_attempt,
    )


def load_resources(state: GraphState, context: OrchestrationContext) -> GraphState:
    curriculum = context.curricula.get_by_id(state.get("curriculum_id") or demo.CURRICULUM_ID)
    knowledge_map = context.knowledge_maps.get_by_id(
        state.get("knowledge_map_id") or demo.KNOWLEDGE_MAP_ID,
    )
    context.agent_services.resource.attach(curriculum, knowledge_map)
    return merge_state(state)


def load_critic_review(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    knowledge_map = context.knowledge_maps.get_by_id(
        state.get("knowledge_map_id") or demo.KNOWLEDGE_MAP_ID,
    )
    curriculum = context.curricula.get_by_id(state.get("curriculum_id") or demo.CURRICULUM_ID)
    attachments = context.resources.list_attachments_by_curriculum_id(curriculum.curriculum_id)
    critic = context.agent_services.critic.review(
        goal,
        knowledge_map,
        curriculum,
        attachments,
        revision_attempt=state.get("critic_revision_attempts", 0),
    )
    return merge_state(
        state,
        critic_review_id=critic.critic_review_id,
        critic_pass_status=critic.pass_status,
        critic_recommendations=list(critic.revision_recommendations[:10]),
    )


def load_progress(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    curriculum = context.curricula.get_by_id(state.get("curriculum_id") or demo.CURRICULUM_ID)
    progress = context.agent_services.progress.build(goal, curriculum)
    return merge_state(state, progress_state_id=progress.progress_state_id)


def load_quiz(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    curriculum = context.curricula.get_by_id(state.get("curriculum_id") or demo.CURRICULUM_ID)
    progress = context.progress.get_by_id(state.get("progress_state_id") or demo.PROGRESS_ID)
    quiz, attempt = context.agent_services.quiz.build(
        goal,
        curriculum,
        progress,
    )
    return merge_state(
        state,
        quiz_id=quiz.quiz_id,
        quiz_attempt_id=attempt.quiz_attempt_id,
        quiz_score=attempt.total_score,
    )


def load_adaptation(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    curriculum = context.curricula.get_by_id(state.get("curriculum_id") or demo.CURRICULUM_ID)
    progress = context.progress.get_by_id(state.get("progress_state_id") or demo.PROGRESS_ID)
    quiz_attempt = context.quizzes.get_attempt_by_id(
        state.get("quiz_attempt_id") or demo.QUIZ_ATTEMPT_ID,
    )
    adaptation = context.agent_services.adaptation.plan(
        goal,
        curriculum,
        progress,
        quiz_attempt,
    )
    return merge_state(state, adaptation_event_ids=[adaptation.adaptation_event_id])


def load_evaluation(state: GraphState, context: OrchestrationContext) -> GraphState:
    goal = _goal_from_state(state, context)
    assessment = context.assessments.get_session_by_id(
        state.get("assessment_session_id") or demo.ASSESSMENT_ID,
    )
    knowledge_map = context.knowledge_maps.get_by_id(
        state.get("knowledge_map_id") or demo.KNOWLEDGE_MAP_ID,
    )
    curriculum = context.curricula.get_by_id(state.get("curriculum_id") or demo.CURRICULUM_ID)
    attachments = context.resources.list_attachments_by_curriculum_id(curriculum.curriculum_id)
    critic = context.critics.get_by_id(state.get("critic_review_id") or demo.CRITIC_REVIEW_ID)
    quiz_attempt = context.quizzes.get_attempt_by_id(
        state.get("quiz_attempt_id") or demo.QUIZ_ATTEMPT_ID,
    )
    adaptation_ids = state.get("adaptation_event_ids", [])
    adaptation_id = adaptation_ids[-1] if adaptation_ids else demo.ADAPTATION_ID
    adaptation = context.adaptations.get_by_id(adaptation_id)
    evaluation = context.agent_services.evaluation.evaluate(
        goal,
        assessment,
        knowledge_map,
        curriculum,
        attachments,
        critic,
        quiz_attempt,
        adaptation,
    )
    return merge_state(state, evaluation_report_id=evaluation.evaluation_report_id)


def prepare_dashboard_payload(state: GraphState, context: OrchestrationContext) -> GraphState:
    context.dashboard.get_by_run_id(state["run_id"])
    context.reporting.get_summary_by_run_id(state["run_id"])
    return merge_state(state)


_REVISION_LIMIT_WARNING_CODE = "curriculum_revision_limit_reached"


def complete_run(state: GraphState, _context: OrchestrationContext) -> GraphState:
    now = _now()
    warnings = list(state.get("warnings", []))
    # Reaching completion with an unresolved critic verdict can only mean the
    # revision cap was hit (the router would otherwise have looped again). The
    # last curriculum is accepted, but the run is flagged so the outcome stays
    # distinguishable from a critic-approved run. The message is generic — it
    # carries no critic recommendation or curriculum content.
    if state.get("critic_pass_status") in (CriticPassStatus.REVISE, CriticPassStatus.FAILED):
        warnings.append(
            WorkflowWarning(
                warning_code=_REVISION_LIMIT_WARNING_CODE,
                message=(
                    "Curriculum accepted after reaching the revision limit "
                    "without critic approval."
                ),
            ),
        )
    return merge_state(
        state,
        status=OrchestrationStatus.COMPLETED,
        current_node="complete_run",
        completed_at=now,
        warnings=warnings,
    )


def _mark_node_completed(
    state: GraphState,
    context: OrchestrationContext,
    node_name: str,
) -> GraphState:
    next_state = merge_state(state, current_node=node_name)
    run = context.orchestration_runs.get_by_id(next_state["run_id"])
    completed_nodes = [*run.completed_nodes]
    if node_name not in completed_nodes:
        completed_nodes.append(node_name)
    warnings = [
        WorkflowWarning.model_validate(warning) for warning in next_state.get("warnings", [])
    ]
    run_status = _run_status_for_state(next_state["status"])
    if run_status == OrchestrationRunStatus.COMPLETED and warnings:
        run_status = OrchestrationRunStatus.COMPLETED_WITH_WARNINGS
    saved_run = run.model_copy(
        update={
            "status": run_status,
            "current_node": node_name,
            "completed_nodes": completed_nodes,
            "artifact_ids": _artifact_ids(next_state),
            "completed_at": next_state.get("completed_at"),
            "warnings": warnings,
            "updated_at": next_state["updated_at"],
        },
        deep=True,
    )
    context.orchestration_runs.save(saved_run)
    context.orchestration_runs.append_event(
        next_state["run_id"],
        node_completed_event(
            run_id=next_state["run_id"],
            node_name=node_name,
            message=_event_message_for_node(node_name, next_state),
        ),
    )
    return next_state


def _mark_node_failed(
    state: GraphState,
    context: OrchestrationContext,
    node_name: str,
    source_error: Exception | None = None,
) -> GraphState:
    error = (
        safe_agent_workflow_error(source_error.agent_name)
        if isinstance(source_error, AgentError)
        else safe_workflow_error(node_name)
    )
    errors = [*state.get("errors", []), error]
    failed_state = merge_state(
        state,
        status=OrchestrationStatus.FAILED,
        current_node=node_name,
        errors=errors,
        completed_at=_now(),
    )
    try:
        run = context.orchestration_runs.get_by_id(failed_state["run_id"])
    except NotFoundError:
        return failed_state

    failed_nodes = [*run.failed_nodes]
    if node_name not in failed_nodes:
        failed_nodes.append(node_name)
    context.orchestration_runs.save(
        run.model_copy(
            update={
                "status": OrchestrationRunStatus.FAILED,
                "current_node": node_name,
                "failed_nodes": failed_nodes,
                "artifact_ids": _artifact_ids(failed_state),
                "completed_at": failed_state["completed_at"],
                "errors": errors,
                "updated_at": failed_state["updated_at"],
            },
            deep=True,
        ),
    )
    context.orchestration_runs.append_event(
        failed_state["run_id"],
        node_failed_event(
            run_id=failed_state["run_id"],
            node_name=node_name,
            error=error,
            message=_event_message_for_node(node_name, failed_state, failed=True),
        ),
    )
    return failed_state


def _goal_from_state(state: GraphState, context: OrchestrationContext):
    return context.goals.get_by_id(state.get("goal_id") or demo.GOAL_ID)


def _create_or_get(
    *,
    create: Callable[[ModelT], ModelT],
    get: Callable[[str], ModelT],
    record: ModelT,
    record_id: str,
) -> ModelT:
    try:
        return create(record)
    except DuplicateRecordError:
        return get(record_id)


def _run_status_for_state(status: OrchestrationStatus) -> OrchestrationRunStatus:
    if status == OrchestrationStatus.COMPLETED:
        return OrchestrationRunStatus.COMPLETED
    if status == OrchestrationStatus.FAILED:
        return OrchestrationRunStatus.FAILED
    if status == OrchestrationStatus.WAITING_FOR_USER:
        return OrchestrationRunStatus.REQUIRES_INPUT
    if status == OrchestrationStatus.QUEUED:
        return OrchestrationRunStatus.CREATED
    return OrchestrationRunStatus.IN_PROGRESS


def _artifact_ids(state: GraphState) -> dict[str, str]:
    artifact_keys = (
        "goal_id",
        "assessment_session_id",
        "knowledge_map_id",
        "curriculum_id",
        "progress_state_id",
        "quiz_id",
        "quiz_attempt_id",
        "critic_review_id",
        "evaluation_report_id",
    )
    artifact_ids = {
        key: value
        for key in artifact_keys
        if isinstance((value := state.get(key)), str)
    }
    adaptation_ids = state.get("adaptation_event_ids", [])
    if adaptation_ids:
        artifact_ids["adaptation_event_id"] = adaptation_ids[-1]
    return artifact_ids


def _event_message_for_node(
    node_name: str,
    state: GraphState,
    *,
    failed: bool = False,
) -> str | None:
    service_name = _service_name_for_node(node_name)
    if service_name is not None:
        pieces = [f"service={service_name}"]
        artifact_id = _artifact_id_for_node(node_name, state)
        if artifact_id:
            pieces.append(f"artifact_id={artifact_id}")
        if failed:
            pieces.append("status=failed")
        return " ".join(pieces)

    agent_name = _agent_name_for_node(node_name)
    if agent_name is None:
        return None
    pieces = [f"agent={agent_name}"]
    artifact_id = _artifact_id_for_node(node_name, state)
    if artifact_id:
        pieces.append(f"artifact_id={artifact_id}")
    if failed:
        pieces.append("status=failed")
    return " ".join(pieces)


def _service_name_for_node(node_name: str) -> str | None:
    if node_name == "prepare_dashboard_payload":
        return None
    return None


def _agent_name_for_node(node_name: str) -> str | None:
    return {
        "load_assessment": "assessment",
        "load_knowledge_map": "knowledge_map",
        "load_curriculum": "curriculum",
        "load_resources": "resource",
        "load_critic_review": "critic",
        "load_progress": "progress",
        "load_quiz": "quiz",
        "load_adaptation": "adapter",
        "load_evaluation": "evaluation",
    }.get(node_name)


def _artifact_id_for_node(node_name: str, state: GraphState) -> str | None:
    if node_name == "load_assessment":
        return state.get("assessment_session_id")
    if node_name == "load_knowledge_map":
        return state.get("knowledge_map_id")
    if node_name == "load_curriculum":
        return state.get("curriculum_id")
    if node_name == "load_resources":
        return "resource_attachments"
    if node_name == "load_critic_review":
        return state.get("critic_review_id")
    if node_name == "load_progress":
        return state.get("progress_state_id")
    if node_name == "load_quiz":
        return state.get("quiz_id")
    if node_name == "load_adaptation":
        adaptation_ids = state.get("adaptation_event_ids", [])
        return adaptation_ids[-1] if adaptation_ids else None
    if node_name == "load_evaluation":
        return state.get("evaluation_report_id")
    if node_name == "prepare_dashboard_payload":
        return "dashboard_summary"
    return None


def _now() -> datetime:
    return datetime.now(tz=UTC)
