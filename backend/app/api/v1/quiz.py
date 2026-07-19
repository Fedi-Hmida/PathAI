from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    QuizServiceDependency,
)
from app.schemas.enums import QuizAttemptStatus
from app.schemas.ids import AttemptId, QuizId
from app.schemas.quiz import (
    LearnerQuizDTO,
    LearnerQuizQuestionDTO,
    QuizAttemptReviewDTO,
    QuizDTO,
    QuizQuestionDTO,
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("/{quiz_id}", response_model=LearnerQuizDTO)
def get_quiz(
    quiz_id: QuizId,
    service: QuizServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> LearnerQuizDTO:
    quiz = service.get_quiz_by_id(quiz_id)
    authz.assert_goal_access(current_user, quiz.goal_id)
    return _to_learner_quiz(quiz)


@router.get("/{quiz_id}/attempts/{attempt_id}", response_model=QuizAttemptReviewDTO)
def get_quiz_attempt_review(
    quiz_id: QuizId,
    attempt_id: AttemptId,
    service: QuizServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> QuizAttemptReviewDTO:
    attempt = service.get_attempt_for_quiz(quiz_id, attempt_id)
    authz.assert_goal_access(current_user, attempt.goal_id)
    quiz = service.get_quiz_by_id(quiz_id)
    questions = (
        quiz.questions
        if attempt.status == QuizAttemptStatus.SCORED
        else _strip_answer_key(quiz.questions)
    )
    return QuizAttemptReviewDTO(attempt=attempt, questions=questions)


def _strip_answer_key(questions: list[QuizQuestionDTO]) -> list[LearnerQuizQuestionDTO]:
    return [
        LearnerQuizQuestionDTO(
            question_id=question.question_id,
            question_type=question.question_type,
            prompt=question.prompt,
            concept_ids=question.concept_ids,
            difficulty=question.difficulty,
            points=question.points,
            options=question.options,
        )
        for question in questions
    ]


def _to_learner_quiz(quiz: QuizDTO) -> LearnerQuizDTO:
    return LearnerQuizDTO(
        quiz_id=quiz.quiz_id,
        title=quiz.title,
        questions=_strip_answer_key(quiz.questions),
        scoring_policy=quiz.scoring_policy,
    )
