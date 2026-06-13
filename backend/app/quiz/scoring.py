import re

from app.quiz.constants import LOW_SCORE_THRESHOLD, PASS_THRESHOLD
from app.quiz.schemas import (
    Quiz,
    QuizAttempt,
    QuizFeedbackItem,
    QuizResult,
    QuizSubmissionRequest,
)


def score_quiz_submission(
    quiz: Quiz,
    submission: QuizSubmissionRequest,
    previous_attempts: list[QuizAttempt],
) -> QuizResult:
    answer_by_question = {
        answer.question_id: answer.answer for answer in submission.answers
    }
    feedback: list[QuizFeedbackItem] = []
    correct_count = 0

    for question in quiz.questions:
        learner_answer = answer_by_question.get(question.question_id, "")
        correct = _is_correct(question.correct_answer, learner_answer)
        if correct:
            correct_count += 1
        feedback.append(
            QuizFeedbackItem(
                question_id=question.question_id,
                correct=correct,
                learner_answer=learner_answer,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                topic_name=question.topic_name,
            )
        )

    score = round(correct_count / len(quiz.questions), 3)
    attempt = QuizAttempt(
        quiz_id=quiz.quiz_id,
        curriculum_id=quiz.curriculum_id,
        week_number=quiz.week_number,
        score=score,
        passed=score >= PASS_THRESHOLD,
        feedback=feedback,
    )
    all_scores = [previous.score for previous in previous_attempts] + [score]
    return QuizResult(
        quiz_id=quiz.quiz_id,
        curriculum_id=quiz.curriculum_id,
        week_number=quiz.week_number,
        score=score,
        passed=attempt.passed,
        best_score=max(all_scores),
        low_score_signal=score < LOW_SCORE_THRESHOLD,
        attempt=attempt,
    )


def _is_correct(expected: str, actual: str) -> bool:
    expected_normalized = _normalize(expected)
    actual_normalized = _normalize(actual)
    if not expected_normalized:
        return False
    return (
        actual_normalized == expected_normalized
        or expected_normalized in actual_normalized
        or actual_normalized in expected_normalized
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())
