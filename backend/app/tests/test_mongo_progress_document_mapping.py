from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.progress import ProgressStateDTO


def test_progress_state_document_round_trip_with_embedded_topic_progress() -> None:
    progress_state = demo.PROGRESS_STATE
    document = to_document(progress_state, progress_state.progress_state_id)

    assert document["_id"] == progress_state.progress_state_id
    assert document["status"] == progress_state.status.value
    assert isinstance(document["topic_progress"], list)
    assert len(document["topic_progress"]) == len(progress_state.topic_progress)
    expected_status = progress_state.topic_progress[0].status.value
    assert document["topic_progress"][0]["status"] == expected_status

    restored = from_document(document, ProgressStateDTO)
    assert restored == progress_state
