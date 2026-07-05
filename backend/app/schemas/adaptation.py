from __future__ import annotations

from pydantic import Field

from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.curriculum import CurriculumChangeDTO, CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import AdaptationStatus, AdaptationTriggerType
from app.schemas.ids import (
    AdaptationId,
    AttemptId,
    ConceptId,
    CurriculumId,
    GoalId,
    TopicId,
)
from app.schemas.progress import ProgressStateDTO, StuckEventDTO
from app.schemas.quiz import QuizAttemptDTO


class AdaptationTrigger(BaseSchema):
    trigger_type: AdaptationTriggerType
    reason: str = Field(min_length=1, max_length=500)
    quiz_attempt_id: AttemptId | None = None
    topic_id: TopicId | None = None
    score: Score | None = None


class AdaptationEventDTO(TimestampedDTO, VersionedDTO):
    adaptation_event_id: AdaptationId
    goal_id: GoalId
    curriculum_id: CurriculumId
    trigger_type: AdaptationTriggerType
    trigger_details: dict[str, str] = Field(default_factory=dict)
    before_summary: str = Field(min_length=1, max_length=1000)
    after_summary: str = Field(min_length=1, max_length=1000)
    changes: list[CurriculumChangeDTO] = Field(min_length=1, max_length=20)
    status: AdaptationStatus
    quiz_attempt_id: AttemptId | None = None
    stuck_event_ids: list[str] = Field(default_factory=list, max_length=20)
    new_curriculum_id: CurriculumId | None = None


class AdaptationAgentInput(BaseSchema):
    goal_text: str = Field(min_length=5, max_length=500)
    curriculum: CurriculumDTO
    progress_state: ProgressStateDTO
    quiz_attempt: QuizAttemptDTO | None = None
    weak_concepts: list[ConceptId] = Field(default_factory=list, max_length=20)
    stuck_events: list[StuckEventDTO] = Field(default_factory=list, max_length=20)


class AdaptationAgentOutput(BaseSchema):
    trigger_reason: str = Field(min_length=1, max_length=500)
    before_summary: str = Field(min_length=1, max_length=1000)
    after_summary: str = Field(min_length=1, max_length=1000)
    changes: list[CurriculumChangeDTO] = Field(min_length=1, max_length=20)
    added_practice_topics: list[CurriculumTopicDTO] = Field(default_factory=list, max_length=10)
    removed_or_deferred_topics: list[TopicId] = Field(default_factory=list, max_length=10)
    expected_benefit: str = Field(min_length=1, max_length=1000)
