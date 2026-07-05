from __future__ import annotations

from app.repositories.fakes.base import InMemoryStore
from app.schemas.enums import QuizAttemptStatus, QuizStatus
from app.schemas.ids import AttemptId, CurriculumId, GoalId, QuizId
from app.schemas.quiz import QuizAttemptDTO, QuizDTO


class FakeQuizRepository:
    def __init__(self) -> None:
        self._quizzes: InMemoryStore[QuizDTO] = InMemoryStore("quiz")
        self._attempts: InMemoryStore[QuizAttemptDTO] = InMemoryStore("quiz attempt")

    def create_quiz(self, quiz: QuizDTO) -> QuizDTO:
        return self._quizzes.create(quiz.quiz_id, quiz)

    def save_quiz(self, quiz: QuizDTO) -> QuizDTO:
        return self._quizzes.save(quiz.quiz_id, quiz)

    def get_quiz_by_id(self, quiz_id: QuizId) -> QuizDTO:
        return self._quizzes.get(quiz_id)

    def list_quizzes_by_goal_id(self, goal_id: GoalId) -> list[QuizDTO]:
        return self._quizzes.list_where("goal_id", goal_id)

    def list_quizzes_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[QuizDTO]:
        return self._quizzes.list_where("curriculum_id", curriculum_id)

    def update_quiz_status(self, quiz_id: QuizId, status: QuizStatus) -> QuizDTO:
        return self._quizzes.update_fields(quiz_id, status=status)

    def create_attempt(self, attempt: QuizAttemptDTO) -> QuizAttemptDTO:
        return self._attempts.create(attempt.quiz_attempt_id, attempt)

    def save_attempt(self, attempt: QuizAttemptDTO) -> QuizAttemptDTO:
        return self._attempts.save(attempt.quiz_attempt_id, attempt)

    def get_attempt_by_id(self, quiz_attempt_id: AttemptId) -> QuizAttemptDTO:
        return self._attempts.get(quiz_attempt_id)

    def list_attempts_by_quiz_id(self, quiz_id: QuizId) -> list[QuizAttemptDTO]:
        return self._attempts.list_where("quiz_id", quiz_id)

    def list_attempts_by_goal_id(self, goal_id: GoalId) -> list[QuizAttemptDTO]:
        return self._attempts.list_where("goal_id", goal_id)

    def list_attempts_by_curriculum_id(
        self,
        curriculum_id: CurriculumId,
    ) -> list[QuizAttemptDTO]:
        return self._attempts.list_where("curriculum_id", curriculum_id)

    def update_attempt_status(
        self,
        quiz_attempt_id: AttemptId,
        status: QuizAttemptStatus,
    ) -> QuizAttemptDTO:
        return self._attempts.update_fields(quiz_attempt_id, status=status)

    def clear(self) -> None:
        self._quizzes.clear()
        self._attempts.clear()
