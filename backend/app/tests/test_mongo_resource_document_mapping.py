from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO


def test_resource_document_round_trip() -> None:
    resource = demo.RESOURCE_CORPUS[0]
    document = to_document(resource, resource.resource_id)

    assert document["_id"] == resource.resource_id
    assert document["status"] == resource.status.value
    assert document["resource_type"] == resource.resource_type.value

    restored = from_document(document, ResourceDTO)
    assert restored == resource


def test_resource_attachment_document_round_trip() -> None:
    attachment = demo.RESOURCE_ATTACHMENTS[0]
    document = to_document(attachment, attachment.attachment_id)

    assert document["_id"] == attachment.attachment_id
    assert document["status"] == attachment.status.value
    assert document["curriculum_id"] == attachment.curriculum_id

    restored = from_document(document, ResourceAttachmentDTO)
    assert restored == attachment
