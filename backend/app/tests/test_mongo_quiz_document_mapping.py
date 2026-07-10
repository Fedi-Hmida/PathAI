from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.quiz import QuizAttemptDTO, QuizDTO


def test_quiz_document_round_trip_with_embedded_questions() -> None:
    quiz = demo.QUIZ
    document = to_document(quiz, quiz.quiz_id)

    assert document["_id"] == quiz.quiz_id
    assert document["status"] == quiz.status.value
    assert isinstance(document["questions"], list)
    assert len(document["questions"]) == len(quiz.questions)
    assert document["questions"][0]["question_type"] == quiz.questions[0].question_type.value

    restored = from_document(document, QuizDTO)
    assert restored == quiz


def test_quiz_attempt_document_round_trip() -> None:
    attempt = demo.QUIZ_ATTEMPT
    document = to_document(attempt, attempt.quiz_attempt_id)

    assert document["_id"] == attempt.quiz_attempt_id
    assert document["quiz_id"] == attempt.quiz_id
    assert document["status"] == attempt.status.value

    restored = from_document(document, QuizAttemptDTO)
    assert restored == attempt
