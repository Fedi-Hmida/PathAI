from typing import Protocol

from app.quiz.errors import QuizNotFoundError
from app.quiz.generator import generate_deterministic_quiz
from app.quiz.llm import generate_quiz_with_optional_mock_llm
from app.quiz.schemas import (
    Quiz,
    QuizGenerateResponse,
    QuizGenerationRequest,
    QuizHistorySummary,
    QuizResult,
    QuizSubmissionRequest,
)
from app.quiz.scoring import score_quiz_submission
from app.repositories import FakeQuizRepository, QuizRepository


class QuizStore(Protocol):
    def save_quiz(self, quiz: Quiz) -> None:
        ...

    def load_quiz(self, quiz_id: str) -> Quiz | None:
        ...

    def save_result(self, result: QuizResult) -> None:
        ...

    def attempts_for_curriculum(self, curriculum_id: str) -> list[QuizResult]:
        ...

    def attempts_for_quiz(self, quiz_id: str) -> list[QuizResult]:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedQuizStore:
    def __init__(self, repository: QuizRepository | None = None) -> None:
        self.repository = repository or FakeQuizRepository()

    def save_quiz(self, quiz: Quiz) -> None:
        self.repository.save_quiz(quiz.model_dump(mode="json"))

    def load_quiz(self, quiz_id: str) -> Quiz | None:
        payload = self.repository.get_quiz(quiz_id)
        if payload is None:
            return None
        return Quiz.model_validate(payload)

    def save_result(self, result: QuizResult) -> None:
        self.repository.save_attempt(result.model_dump(mode="json"))

    def attempts_for_curriculum(self, curriculum_id: str) -> list[QuizResult]:
        return [
            QuizResult.model_validate(payload)
            for payload in self.repository.get_history(curriculum_id)
        ]

    def attempts_for_quiz(self, quiz_id: str) -> list[QuizResult]:
        quiz_payload = self.repository.get_quiz(quiz_id)
        if quiz_payload is None:
            return []
        curriculum_id = quiz_payload.get("curriculum_id")
        if not isinstance(curriculum_id, str):
            return []
        return [
            QuizResult.model_validate(payload)
            for payload in self.repository.get_history(curriculum_id)
            if payload.get("quiz_id") == quiz_id
        ]

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryQuizStore(RepositoryBackedQuizStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeQuizRepository())


class QuizService:
    def __init__(
        self,
        store: QuizStore | None = None,
        repository: QuizRepository | None = None,
    ) -> None:
        self.store = store or RepositoryBackedQuizStore(repository)

    async def generate_quiz(
        self,
        request: QuizGenerationRequest,
    ) -> QuizGenerateResponse:
        deterministic = generate_deterministic_quiz(request)
        quiz = await generate_quiz_with_optional_mock_llm(request, deterministic)
        self.store.save_quiz(quiz)
        return QuizGenerateResponse(quiz=quiz)

    def get_quiz(self, quiz_id: str) -> Quiz:
        quiz = self.store.load_quiz(quiz_id)
        if quiz is None:
            raise QuizNotFoundError(
                code="quiz_not_found",
                message=f"Quiz '{quiz_id}' was not found.",
                status_code=404,
            )
        return quiz

    def submit_quiz(
        self,
        quiz_id: str,
        submission: QuizSubmissionRequest,
    ) -> QuizResult:
        quiz = self.get_quiz(quiz_id)
        previous_attempts = [
            result.attempt for result in self.store.attempts_for_quiz(quiz_id)
        ]
        result = score_quiz_submission(quiz, submission, previous_attempts)
        self.store.save_result(result)
        return result

    def get_history(self, curriculum_id: str) -> QuizHistorySummary:
        results = self.store.attempts_for_curriculum(curriculum_id)
        attempts = [result.attempt for result in results]
        scores = [attempt.score for attempt in attempts]
        return QuizHistorySummary(
            curriculum_id=curriculum_id,
            attempts=attempts,
            best_score=max(scores) if scores else None,
            average_score=round(sum(scores) / len(scores), 3) if scores else None,
            low_score_count=sum(1 for result in results if result.low_score_signal),
        )
