from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.curriculum import CurriculumDTO


def test_curriculum_document_round_trip_with_nested_weeks_and_topics() -> None:
    curriculum = demo.CURRICULUM
    document = to_document(curriculum, curriculum.curriculum_id)

    assert document["_id"] == curriculum.curriculum_id
    assert document["status"] == curriculum.status.value
    assert isinstance(document["weeks"], list)
    assert len(document["weeks"]) == len(curriculum.weeks)

    first_week_document = document["weeks"][0]
    first_week_dto = curriculum.weeks[0]
    assert isinstance(first_week_document["topics"], list)
    assert len(first_week_document["topics"]) == len(first_week_dto.topics)
    expected_difficulty = first_week_dto.topics[0].difficulty.value
    assert first_week_document["topics"][0]["difficulty"] == expected_difficulty

    restored = from_document(document, CurriculumDTO)
    assert restored == curriculum
