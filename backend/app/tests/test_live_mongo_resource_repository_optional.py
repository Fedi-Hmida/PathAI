from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoResourceRepository
from app.schemas.enums import (
    DifficultyLevel,
    ResourceAttachmentStatus,
    ResourceStatus,
    ResourceType,
)
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def resource_repository() -> Iterator[MongoResourceRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    database = client[settings.mongodb_database_name]
    repository = MongoResourceRepository(
        database["test_17f_resources"],
        database["test_17f_resource_attachments"],
    )
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_resource(resource_id: str) -> ResourceDTO:
    now = datetime.now(tz=UTC)
    return ResourceDTO(
        resource_id=resource_id,
        title="Designing Data-Intensive Applications, Ch. 5",
        resource_type=ResourceType.ARTICLE,
        source_name="live mongo test corpus",
        url="https://example.invalid/ddia-ch5",
        topic_tags=["replication"],
        concept_ids=["distributed_systems"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=45,
        quality_score=0.9,
        license_note="Fair use excerpt for testing.",
        created_at=now,
        updated_at=now,
    )


def _sample_attachment(
    attachment_id: str,
    goal_id: str,
    curriculum_id: str,
    topic_id: str,
    resource_id: str,
) -> ResourceAttachmentDTO:
    now = datetime.now(tz=UTC)
    return ResourceAttachmentDTO(
        attachment_id=attachment_id,
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        topic_id=topic_id,
        resource_id=resource_id,
        rank=1,
        relevance_score=0.8,
        selection_reason="Directly covers the target concept.",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_resource_create_get_and_duplicate(
    resource_repository: MongoResourceRepository,
) -> None:
    resource = _sample_resource("resource_live17f_a")

    created = resource_repository.create_resource(resource)
    assert created.resource_id == resource.resource_id

    fetched = resource_repository.get_resource_by_id(resource.resource_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        resource_repository.create_resource(resource)

    updated = resource_repository.update_resource_status(
        resource.resource_id,
        ResourceStatus.DEPRECATED,
    )
    assert updated.status == ResourceStatus.DEPRECATED

    assert len(resource_repository.list_resources()) == 1


@pytest.mark.live_mongo
def test_attachment_lifecycle_and_list_by_methods(
    resource_repository: MongoResourceRepository,
) -> None:
    resource = _sample_resource("resource_live17f_b")
    resource_repository.create_resource(resource)

    attachment = _sample_attachment(
        "attach_live17f_b",
        "goal_live17f_b",
        "curriculum_live17f_b",
        "topic_live17f_b",
        resource.resource_id,
    )
    resource_repository.create_attachment(attachment)

    assert len(resource_repository.list_attachments_by_goal_id(attachment.goal_id)) == 1
    assert len(
        resource_repository.list_attachments_by_curriculum_id(attachment.curriculum_id),
    ) == 1
    assert len(resource_repository.list_attachments_by_topic_id(attachment.topic_id)) == 1

    updated = resource_repository.update_attachment_status(
        attachment.attachment_id,
        ResourceAttachmentStatus.SUPERSEDED,
    )
    assert updated.status == ResourceAttachmentStatus.SUPERSEDED
