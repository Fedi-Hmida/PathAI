from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.knowledge_map import KnowledgeMapDTO


def test_knowledge_map_document_round_trip() -> None:
    knowledge_map = demo.KNOWLEDGE_MAP
    document = to_document(knowledge_map, knowledge_map.knowledge_map_id)

    assert document["_id"] == knowledge_map.knowledge_map_id
    assert document["status"] == knowledge_map.status.value
    assert isinstance(document["concepts"], list)
    assert len(document["concepts"]) == len(knowledge_map.concepts)
    expected_classification = knowledge_map.concepts[0].classification.value
    assert document["concepts"][0]["classification"] == expected_classification

    restored = from_document(document, KnowledgeMapDTO)
    assert restored == knowledge_map
