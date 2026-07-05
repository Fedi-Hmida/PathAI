from __future__ import annotations

from typing import Protocol

from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.enums import AdaptationStatus
from app.schemas.ids import AdaptationId, AttemptId, CurriculumId, GoalId


class AdaptationRepository(Protocol):
    def create(self, adaptation_event: AdaptationEventDTO) -> AdaptationEventDTO: ...

    def save(self, adaptation_event: AdaptationEventDTO) -> AdaptationEventDTO: ...

    def get_by_id(self, adaptation_event_id: AdaptationId) -> AdaptationEventDTO: ...

    def list_by_goal_id(self, goal_id: GoalId) -> list[AdaptationEventDTO]: ...

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[AdaptationEventDTO]: ...

    def list_by_quiz_attempt_id(self, quiz_attempt_id: AttemptId) -> list[AdaptationEventDTO]: ...

    def update_status(
        self,
        adaptation_event_id: AdaptationId,
        status: AdaptationStatus,
    ) -> AdaptationEventDTO: ...

    def clear(self) -> None: ...
