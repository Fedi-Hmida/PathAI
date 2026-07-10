from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.adaptation import AdaptationEventDTO


def test_adaptation_event_document_round_trip_with_embedded_changes() -> None:
    adaptation_event = demo.ADAPTATION_EVENT
    document = to_document(adaptation_event, adaptation_event.adaptation_event_id)

    assert document["_id"] == adaptation_event.adaptation_event_id
    assert document["status"] == adaptation_event.status.value
    assert isinstance(document["changes"], list)
    assert len(document["changes"]) == len(adaptation_event.changes)
    expected_change_type = adaptation_event.changes[0].change_type.value
    assert document["changes"][0]["change_type"] == expected_change_type

    restored = from_document(document, AdaptationEventDTO)
    assert restored == adaptation_event
