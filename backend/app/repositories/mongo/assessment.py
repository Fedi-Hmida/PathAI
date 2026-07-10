from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.assessment import AssessmentAnswerDTO, AssessmentSessionDTO
from app.schemas.enums import AssessmentStatus
from app.schemas.ids import AnswerId, AssessmentId, GoalId, RunId


class MongoAssessmentRepository:
    def __init__(
        self,
        sessions_collection: Collection[dict[str, Any]],
        answers_collection: Collection[dict[str, Any]],
    ) -> None:
        self._sessions: MongoStore[AssessmentSessionDTO] = MongoStore(
            sessions_collection,
            AssessmentSessionDTO,
            "assessment session",
        )
        self._answers: MongoStore[AssessmentAnswerDTO] = MongoStore(
            answers_collection,
            AssessmentAnswerDTO,
            "assessment answer",
        )

    def create_session(self, session: AssessmentSessionDTO) -> AssessmentSessionDTO:
        return self._sessions.create(session.assessment_session_id, session)

    def save_session(self, session: AssessmentSessionDTO) -> AssessmentSessionDTO:
        return self._sessions.save(session.assessment_session_id, session)

    def get_session_by_id(self, assessment_session_id: AssessmentId) -> AssessmentSessionDTO:
        return self._sessions.get(assessment_session_id)

    def list_sessions_by_goal_id(self, goal_id: GoalId) -> list[AssessmentSessionDTO]:
        return self._sessions.list_where("goal_id", goal_id)

    def list_sessions_by_run_id(self, run_id: RunId) -> list[AssessmentSessionDTO]:
        return self._sessions.list_where("run_id", run_id)

    def update_session_status(
        self,
        assessment_session_id: AssessmentId,
        status: AssessmentStatus,
    ) -> AssessmentSessionDTO:
        return self._sessions.update_fields(assessment_session_id, status=status)

    def create_answer(self, answer: AssessmentAnswerDTO) -> AssessmentAnswerDTO:
        return self._answers.create(answer.answer_id, answer)

    def save_answer(self, answer: AssessmentAnswerDTO) -> AssessmentAnswerDTO:
        return self._answers.save(answer.answer_id, answer)

    def get_answer_by_id(self, answer_id: AnswerId) -> AssessmentAnswerDTO:
        return self._answers.get(answer_id)

    def list_answers_by_session_id(
        self,
        assessment_session_id: AssessmentId,
    ) -> list[AssessmentAnswerDTO]:
        return self._answers.list_where("assessment_session_id", assessment_session_id)

    def list_answers_by_goal_id(self, goal_id: GoalId) -> list[AssessmentAnswerDTO]:
        return self._answers.list_where("goal_id", goal_id)

    def clear(self) -> None:
        self._sessions.clear()
        self._answers.clear()
