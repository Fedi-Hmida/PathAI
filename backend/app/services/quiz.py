from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.quiz import QuizRepository
from app.schemas.enums import QuizAttemptStatus, QuizStatus
from app.schemas.ids import AttemptId, CurriculumId, GoalId, QuizId
from app.schemas.quiz import QuizAttemptDTO, QuizDTO


@dataclass(slots=True)
class QuizService:
    repository: QuizRepository

    def create_quiz(self, quiz: QuizDTO) -> QuizDTO:
        return self.repository.create_quiz(quiz)

    def save_quiz(self, quiz: QuizDTO) -> QuizDTO:
        return self.repository.save_quiz(quiz)

    def get_quiz_by_id(self, quiz_id: QuizId) -> QuizDTO:
        return self.repository.get_quiz_by_id(quiz_id)

    def list_quizzes_by_goal_id(self, goal_id: GoalId) -> list[QuizDTO]:
        return self.repository.list_quizzes_by_goal_id(goal_id)

    def list_quizzes_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[QuizDTO]:
        return self.repository.list_quizzes_by_curriculum_id(curriculum_id)

    def update_quiz_status(self, quiz_id: QuizId, status: QuizStatus) -> QuizDTO:
        return self.repository.update_quiz_status(quiz_id, status)

    def create_attempt(self, attempt: QuizAttemptDTO) -> QuizAttemptDTO:
        return self.repository.create_attempt(attempt)

    def save_attempt(self, attempt: QuizAttemptDTO) -> QuizAttemptDTO:
        return self.repository.save_attempt(attempt)

    def get_attempt_by_id(self, quiz_attempt_id: AttemptId) -> QuizAttemptDTO:
        return self.repository.get_attempt_by_id(quiz_attempt_id)

    def list_attempts_by_quiz_id(self, quiz_id: QuizId) -> list[QuizAttemptDTO]:
        return self.repository.list_attempts_by_quiz_id(quiz_id)

    def list_attempts_by_goal_id(self, goal_id: GoalId) -> list[QuizAttemptDTO]:
        return self.repository.list_attempts_by_goal_id(goal_id)

    def list_attempts_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[QuizAttemptDTO]:
        return self.repository.list_attempts_by_curriculum_id(curriculum_id)

    def update_attempt_status(
        self,
        quiz_attempt_id: AttemptId,
        status: QuizAttemptStatus,
    ) -> QuizAttemptDTO:
        return self.repository.update_attempt_status(quiz_attempt_id, status)
