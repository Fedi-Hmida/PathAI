"""Instantiate a fresh, per-user copy of the canonical demo workspace.

The canonical demo (`canonical_demo.py`) is a single fixed graph of artifacts
that all cross-reference each other by ID. To give each authenticated user their
own isolated workspace, we clone that graph with a fresh set of IDs so multiple
users can coexist without collisions, and stamp the owner on the two roots (goal
and run). Everything else is authorized transitively via ``goal_id``.

The re-ID is field-name-aware: it rewrites only the values of ID-typed fields
(those named ``*_id`` / ``*_ids`` / ``artifact_ids``). Shared references are
excluded by name — ``resource_id`` (the curated corpus) and any ``concept*``
field (shared vocabulary) are left untouched — as are non-ID strings such as
enum values and workflow node names, which a naive string scan would wrongly
rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from app.fixtures import canonical_demo as demo
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.critic import CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.ids import UserId
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.orchestration import OrchestrationRunDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAttemptDTO, QuizDTO
from app.schemas.resource import ResourceAttachmentDTO

# ID fields whose values reference shared, non-workspace data and must NOT be
# re-IDed. ``resource_id`` points at the shared curated corpus; any field with
# "concept" in its name holds shared concept vocabulary.
_SHARED_ID_FIELDS = frozenset({"resource_id"})

ModelT = TypeVar("ModelT", bound=BaseModel)


def _is_workspace_id_field(field_name: str) -> bool:
    if "concept" in field_name or field_name in _SHARED_ID_FIELDS:
        return False
    return field_name.endswith(("_id", "_ids")) or field_name == "artifact_ids"


@dataclass(slots=True)
class WorkspaceBundle:
    goal: LearningGoalDTO
    run: OrchestrationRunDTO
    knowledge_map: KnowledgeMapDTO
    curriculum: CurriculumDTO
    resource_attachments: list[ResourceAttachmentDTO]
    progress_state: ProgressStateDTO
    quiz: QuizDTO
    quiz_attempt: QuizAttemptDTO
    adaptation_event: AdaptationEventDTO
    critic_review: CriticReviewDTO
    evaluation_report: EvaluationReportDTO

    @property
    def run_id(self) -> str:
        return self.run.run_id

    @property
    def goal_id(self) -> str:
        return self.goal.goal_id


def build_user_workspace(
    owner_user_id: UserId,
    *,
    goal_text: str,
    learner_profile: LearnerProfile | None = None,
) -> WorkspaceBundle:
    """Return a fully re-IDed, owner-stamped clone of the canonical demo,
    with the caller's own goal text (and, optionally, learner profile)
    substituted in place of the demo's. Everything else (knowledge map,
    curriculum, quiz, critic review, evaluation) still starts as demo-clone
    placeholder content until the live assessment completes and
    `WorkspaceGenerationService` regenerates it for real."""
    source_run = _source_run()
    # No assessment session/answers here: a freshly seeded workspace has no
    # assessment session at all - the learner takes a real, live one via
    # POST /me/assessment/start. demo.KNOWLEDGE_MAP.assessment_session_id
    # still gets collected below (its own field triggers collection) and
    # consistently re-IDed, even though nothing is cloned under that ID - a
    # dangling reference DashboardService already tolerates.
    single_sources: list[BaseModel] = [
        demo.LEARNING_GOAL,
        source_run,
        demo.KNOWLEDGE_MAP,
        demo.CURRICULUM,
        demo.PROGRESS_STATE,
        demo.QUIZ,
        demo.QUIZ_ATTEMPT,
        demo.ADAPTATION_EVENT,
        demo.CRITIC_REVIEW,
        demo.EVALUATION_REPORT,
    ]
    list_sources: list[BaseModel] = [*demo.RESOURCE_ATTACHMENTS]

    found: set[str] = set()
    for dto in [*single_sources, *list_sources]:
        _collect_ids(dto.model_dump(mode="json"), found)
    id_map = {old_id: _new_id(old_id) for old_id in found}

    goal_overrides: dict[str, Any] = {
        "owner_user_id": owner_user_id,
        "goal_text": goal_text,
        "normalized_goal_text": " ".join(goal_text.split()),
    }
    if learner_profile is not None:
        goal_overrides["learner_profile"] = learner_profile.model_dump(mode="json")

    return WorkspaceBundle(
        goal=_rebuild(demo.LEARNING_GOAL, id_map, **goal_overrides),
        run=_rebuild(source_run, id_map, owner_user_id=owner_user_id),
        knowledge_map=_rebuild(demo.KNOWLEDGE_MAP, id_map),
        curriculum=_rebuild(demo.CURRICULUM, id_map),
        resource_attachments=[_rebuild(a, id_map) for a in demo.RESOURCE_ATTACHMENTS],
        progress_state=_rebuild(demo.PROGRESS_STATE, id_map),
        quiz=_rebuild(demo.QUIZ, id_map),
        quiz_attempt=_rebuild(demo.QUIZ_ATTEMPT, id_map),
        adaptation_event=_rebuild(demo.ADAPTATION_EVENT, id_map),
        critic_review=_rebuild(demo.CRITIC_REVIEW, id_map),
        evaluation_report=_rebuild(demo.EVALUATION_REPORT, id_map),
    )


def _source_run() -> OrchestrationRunDTO:
    """The canonical completed run, with the demo IDs so it re-IDs alongside
    the rest of the graph (mirrors ``_canonical_orchestration_run`` in the API
    container)."""
    return OrchestrationRunDTO(
        run_id=demo.RUN_ID,
        goal_id=demo.GOAL_ID,
        workflow_version="demo-v1",
        status=OrchestrationRunStatus.COMPLETED,
        current_node="prepare_dashboard_payload",
        completed_nodes=[
            "goal_loaded",
            "assessment_loaded",
            "knowledge_map_loaded",
            "curriculum_loaded",
            "dashboard_loaded",
        ],
        failed_nodes=[],
        node_events=[],
        artifact_ids={
            "goal_id": demo.GOAL_ID,
            "assessment_id": demo.ASSESSMENT_ID,
            "knowledge_map_id": demo.KNOWLEDGE_MAP_ID,
            "curriculum_id": demo.CURRICULUM_ID,
            "progress_id": demo.PROGRESS_ID,
            "quiz_id": demo.QUIZ_ID,
            "quiz_attempt_id": demo.QUIZ_ATTEMPT_ID,
            "adaptation_id": demo.ADAPTATION_ID,
            "critic_id": demo.CRITIC_REVIEW_ID,
            "evaluation_id": demo.EVALUATION_REPORT_ID,
        },
        started_at=demo.NOW,
        completed_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _new_id(old_id: str) -> str:
    prefix = old_id[: old_id.index("_") + 1]
    return f"{prefix}{uuid4().hex}"


def _collect_ids(node: Any, found: set[str]) -> None:
    """Collect every string that is the value of a workspace-scoped ID field."""
    if isinstance(node, dict):
        for key, value in node.items():
            if _is_workspace_id_field(key):
                _collect_id_values(value, found)
            else:
                _collect_ids(value, found)
    elif isinstance(node, list):
        for value in node:
            _collect_ids(value, found)


def _collect_id_values(value: Any, found: set[str]) -> None:
    if isinstance(value, str):
        found.add(value)
    elif isinstance(value, list):
        for item in value:
            _collect_id_values(item, found)
    elif isinstance(value, dict):
        # e.g. artifact_ids: label -> id; only the values are IDs.
        for item in value.values():
            _collect_id_values(item, found)


def _remap_ids(node: Any, id_map: dict[str, str]) -> Any:
    if isinstance(node, dict):
        return {
            key: (
                _remap_id_values(value, id_map)
                if _is_workspace_id_field(key)
                else _remap_ids(value, id_map)
            )
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [_remap_ids(value, id_map) for value in node]
    return node


def _remap_id_values(value: Any, id_map: dict[str, str]) -> Any:
    if isinstance(value, str):
        return id_map.get(value, value)
    if isinstance(value, list):
        return [_remap_id_values(item, id_map) for item in value]
    if isinstance(value, dict):
        return {key: _remap_id_values(item, id_map) for key, item in value.items()}
    return value


def _rebuild(dto: ModelT, id_map: dict[str, str], **overrides: Any) -> ModelT:
    data = _remap_ids(dto.model_dump(mode="json"), id_map)
    data.update(overrides)
    return type(dto).model_validate(data)
