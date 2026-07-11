from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    QuizServiceDependency,
)
from app.schemas.ids import QuizId
from app.schemas.quiz import LearnerQuizDTO, LearnerQuizQuestionDTO, QuizDTO

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


def _to_learner_quiz(quiz: QuizDTO) -> LearnerQuizDTO:
    return LearnerQuizDTO(
        quiz_id=quiz.quiz_id,
        title=quiz.title,
        questions=[
            LearnerQuizQuestionDTO(
                question_id=question.question_id,
                question_type=question.question_type,
                prompt=question.prompt,
                concept_ids=question.concept_ids,
                difficulty=question.difficulty,
                points=question.points,
                options=question.options,
            )
            for question in quiz.questions
        ],
        scoring_policy=quiz.scoring_policy,
    )
