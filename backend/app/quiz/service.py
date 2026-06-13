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


class InMemoryQuizStore:
    def __init__(self) -> None:
        self._quizzes: dict[str, Quiz] = {}
        self._attempts: dict[str, list[QuizResult]] = {}

    def save_quiz(self, quiz: Quiz) -> None:
        self._quizzes[quiz.quiz_id] = quiz.model_copy(deep=True)

    def load_quiz(self, quiz_id: str) -> Quiz | None:
        quiz = self._quizzes.get(quiz_id)
        if quiz is None:
            return None
        return quiz.model_copy(deep=True)

    def save_result(self, result: QuizResult) -> None:
        self._attempts.setdefault(result.curriculum_id, []).append(
            result.model_copy(deep=True)
        )

    def attempts_for_curriculum(self, curriculum_id: str) -> list[QuizResult]:
        return [
            attempt.model_copy(deep=True)
            for attempt in self._attempts.get(curriculum_id, [])
        ]

    def attempts_for_quiz(self, quiz_id: str) -> list[QuizResult]:
        return [
            attempt.model_copy(deep=True)
            for attempts in self._attempts.values()
            for attempt in attempts
            if attempt.quiz_id == quiz_id
        ]

    def clear(self) -> None:
        self._quizzes.clear()
        self._attempts.clear()


class QuizService:
    def __init__(self, store: InMemoryQuizStore | None = None) -> None:
        self.store = store or InMemoryQuizStore()

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
