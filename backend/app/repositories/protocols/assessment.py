from __future__ import annotations

from typing import Protocol

from app.schemas.assessment import AssessmentAnswerDTO, AssessmentSessionDTO
from app.schemas.enums import AssessmentStatus
from app.schemas.ids import AnswerId, AssessmentId, GoalId, RunId


class AssessmentRepository(Protocol):
    def create_session(self, session: AssessmentSessionDTO) -> AssessmentSessionDTO: ...

    def save_session(self, session: AssessmentSessionDTO) -> AssessmentSessionDTO: ...

    def get_session_by_id(self, assessment_session_id: AssessmentId) -> AssessmentSessionDTO: ...

    def list_sessions_by_goal_id(self, goal_id: GoalId) -> list[AssessmentSessionDTO]: ...

    def list_sessions_by_run_id(self, run_id: RunId) -> list[AssessmentSessionDTO]: ...

    def update_session_status(
        self,
        assessment_session_id: AssessmentId,
        status: AssessmentStatus,
    ) -> AssessmentSessionDTO: ...

    def create_answer(self, answer: AssessmentAnswerDTO) -> AssessmentAnswerDTO: ...

    def save_answer(self, answer: AssessmentAnswerDTO) -> AssessmentAnswerDTO: ...

    def get_answer_by_id(self, answer_id: AnswerId) -> AssessmentAnswerDTO: ...

    def list_answers_by_session_id(
        self,
        assessment_session_id: AssessmentId,
    ) -> list[AssessmentAnswerDTO]: ...

    def list_answers_by_goal_id(self, goal_id: GoalId) -> list[AssessmentAnswerDTO]: ...

    def clear(self) -> None: ...
