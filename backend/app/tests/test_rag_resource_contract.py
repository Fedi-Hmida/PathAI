from pathlib import Path

import pytest
from pydantic import ValidationError

from app.rag.resource_loader import (
    ResourceSeedValidationError,
    load_json_object,
    load_resource_seed,
    map_seed_to_document_payload,
    validate_resource_seed_against_json_schema,
)
from app.rag.schemas import ResourceSeed

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_SCHEMA_PATH = PROJECT_ROOT / "rag" / "schemas" / "resource.schema.json"
SAMPLE_RESOURCE_PATH = (
    PROJECT_ROOT / "rag" / "resources" / "staging" / "resource_rag_seed_sample.json"
)


def test_sample_resource_seed_validates_against_json_schema() -> None:
    schema = load_json_object(RESOURCE_SCHEMA_PATH)
    payload = load_json_object(SAMPLE_RESOURCE_PATH)

    validate_resource_seed_against_json_schema(payload, schema)


def test_sample_resource_seed_maps_to_backend_resource_payload() -> None:
    schema = load_json_object(RESOURCE_SCHEMA_PATH)
    seed = load_resource_seed(SAMPLE_RESOURCE_PATH, schema)
    mapped = map_seed_to_document_payload(seed)

    assert mapped.title == seed.title
    assert mapped.estimated_minutes == seed.estimated_time_minutes
    assert mapped.source_name == seed.source
    assert mapped.source_domain == "arxiv.org"
    assert mapped.access == "free"
    assert mapped.type == "paper"
    assert mapped.foundational is True
    assert mapped.last_verified_at is not None


def test_resource_seed_schema_rejects_missing_required_field() -> None:
    schema = load_json_object(RESOURCE_SCHEMA_PATH)
    payload = load_json_object(SAMPLE_RESOURCE_PATH)
    payload.pop("title")

    with pytest.raises(ResourceSeedValidationError, match="missing fields"):
        validate_resource_seed_against_json_schema(payload, schema)


def test_resource_seed_schema_rejects_invalid_enum_value() -> None:
    schema = load_json_object(RESOURCE_SCHEMA_PATH)
    payload = load_json_object(SAMPLE_RESOURCE_PATH)
    payload["difficulty"] = "expert"

    with pytest.raises(ResourceSeedValidationError, match="difficulty"):
        validate_resource_seed_against_json_schema(payload, schema)

    with pytest.raises(ValidationError):
        ResourceSeed.model_validate(payload)
