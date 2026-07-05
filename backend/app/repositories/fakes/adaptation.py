from __future__ import annotations

from app.repositories.fakes.base import InMemoryStore
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.enums import AdaptationStatus
from app.schemas.ids import AdaptationId, AttemptId, CurriculumId, GoalId


class FakeAdaptationRepository:
    def __init__(self) -> None:
        self._adaptation_events: InMemoryStore[AdaptationEventDTO] = InMemoryStore(
            "adaptation event",
        )

    def create(self, adaptation_event: AdaptationEventDTO) -> AdaptationEventDTO:
        return self._adaptation_events.create(
            adaptation_event.adaptation_event_id,
            adaptation_event,
        )

    def save(self, adaptation_event: AdaptationEventDTO) -> AdaptationEventDTO:
        return self._adaptation_events.save(
            adaptation_event.adaptation_event_id,
            adaptation_event,
        )

    def get_by_id(self, adaptation_event_id: AdaptationId) -> AdaptationEventDTO:
        return self._adaptation_events.get(adaptation_event_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[AdaptationEventDTO]:
        return self._adaptation_events.list_where("goal_id", goal_id)

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[AdaptationEventDTO]:
        return self._adaptation_events.list_where("curriculum_id", curriculum_id)

    def list_by_quiz_attempt_id(self, quiz_attempt_id: AttemptId) -> list[AdaptationEventDTO]:
        return self._adaptation_events.list_where("quiz_attempt_id", quiz_attempt_id)

    def update_status(
        self,
        adaptation_event_id: AdaptationId,
        status: AdaptationStatus,
    ) -> AdaptationEventDTO:
        return self._adaptation_events.update_fields(adaptation_event_id, status=status)

    def clear(self) -> None:
        self._adaptation_events.clear()
