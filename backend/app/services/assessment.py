from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.assessment import AssessmentRepository
from app.schemas.assessment import AssessmentAnswerDTO, AssessmentSessionDTO
from app.schemas.enums import AssessmentStatus
from app.schemas.ids import AnswerId, AssessmentId, GoalId, RunId


@dataclass(slots=True)
class AssessmentService:
    repository: AssessmentRepository

    def create_session(self, session: AssessmentSessionDTO) -> AssessmentSessionDTO:
        return self.repository.create_session(session)

    def save_session(self, session: AssessmentSessionDTO) -> AssessmentSessionDTO:
        return self.repository.save_session(session)

    def get_session_by_id(self, assessment_session_id: AssessmentId) -> AssessmentSessionDTO:
        return self.repository.get_session_by_id(assessment_session_id)

    def list_sessions_by_goal_id(self, goal_id: GoalId) -> list[AssessmentSessionDTO]:
        return self.repository.list_sessions_by_goal_id(goal_id)

    def list_sessions_by_run_id(self, run_id: RunId) -> list[AssessmentSessionDTO]:
        return self.repository.list_sessions_by_run_id(run_id)

    def update_session_status(
        self,
        assessment_session_id: AssessmentId,
        status: AssessmentStatus,
    ) -> AssessmentSessionDTO:
        return self.repository.update_session_status(assessment_session_id, status)

    def create_answer(self, answer: AssessmentAnswerDTO) -> AssessmentAnswerDTO:
        return self.repository.create_answer(answer)

    def save_answer(self, answer: AssessmentAnswerDTO) -> AssessmentAnswerDTO:
        return self.repository.save_answer(answer)

    def get_answer_by_id(self, answer_id: AnswerId) -> AssessmentAnswerDTO:
        return self.repository.get_answer_by_id(answer_id)

    def list_answers_by_session_id(
        self,
        assessment_session_id: AssessmentId,
    ) -> list[AssessmentAnswerDTO]:
        return self.repository.list_answers_by_session_id(assessment_session_id)

    def list_answers_by_goal_id(self, goal_id: GoalId) -> list[AssessmentAnswerDTO]:
        return self.repository.list_answers_by_goal_id(goal_id)
