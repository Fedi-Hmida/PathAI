from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.assessment import AssessmentAnswerDTO, AssessmentSessionDTO


def test_assessment_session_document_round_trip() -> None:
    session = demo.ASSESSMENT_SESSION
    document = to_document(session, session.assessment_session_id)

    assert document["_id"] == session.assessment_session_id
    assert document["status"] == session.status.value
    assert isinstance(document["started_at"], str)

    restored = from_document(document, AssessmentSessionDTO)
    assert restored == session


def test_assessment_answer_document_round_trip() -> None:
    answer = demo.ASSESSMENT_ANSWERS[0]
    document = to_document(answer, answer.answer_id)

    assert document["_id"] == answer.answer_id
    assert document["assessment_session_id"] == answer.assessment_session_id
    assert isinstance(document["question"], dict)

    restored = from_document(document, AssessmentAnswerDTO)
    assert restored == answer
