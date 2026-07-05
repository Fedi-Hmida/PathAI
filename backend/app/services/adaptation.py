from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.adaptation import AdaptationRepository
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.enums import AdaptationStatus
from app.schemas.ids import AdaptationId, AttemptId, CurriculumId, GoalId


@dataclass(slots=True)
class AdaptationService:
    repository: AdaptationRepository

    def create(self, adaptation_event: AdaptationEventDTO) -> AdaptationEventDTO:
        return self.repository.create(adaptation_event)

    def save(self, adaptation_event: AdaptationEventDTO) -> AdaptationEventDTO:
        return self.repository.save(adaptation_event)

    def get_by_id(self, adaptation_event_id: AdaptationId) -> AdaptationEventDTO:
        return self.repository.get_by_id(adaptation_event_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[AdaptationEventDTO]:
        return self.repository.list_by_goal_id(goal_id)

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[AdaptationEventDTO]:
        return self.repository.list_by_curriculum_id(curriculum_id)

    def list_by_quiz_attempt_id(self, quiz_attempt_id: AttemptId) -> list[AdaptationEventDTO]:
        return self.repository.list_by_quiz_attempt_id(quiz_attempt_id)

    def update_status(
        self,
        adaptation_event_id: AdaptationId,
        status: AdaptationStatus,
    ) -> AdaptationEventDTO:
        return self.repository.update_status(adaptation_event_id, status)
