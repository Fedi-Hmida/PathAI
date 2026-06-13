from pathlib import Path

import pytest

from app.rag.curation import (
    build_catalog_items_from_seeds,
    canonical_resource_directories,
    load_canonical_resource_seeds,
    load_resource_schema,
    validate_seed_payload,
)
from app.rag.resource_loader import (
    ResourceSeedValidationError,
    load_resource_seeds_from_directory,
)
from app.rag.service import ResourceService


def test_loads_canonical_resource_seeds_from_rag_resources() -> None:
    seeds = load_canonical_resource_seeds()

    assert len(seeds) >= 4
    assert all(seed.url.startswith("https://") for seed in seeds)
    assert {path.name for path in canonical_resource_directories()} == {"staging", "approved"}


def test_build_catalog_deduplicates_by_url_and_derives_resource_ids() -> None:
    seeds = load_canonical_resource_seeds()
    catalog = build_catalog_items_from_seeds([*seeds, seeds[0]])

    urls = [item.url for item in catalog]
    assert len(urls) == len(set(urls))
    assert all(item.resource_id.startswith("res_") for item in catalog)
    assert all(item.source_domain for item in catalog)


def test_catalog_summary_exposes_topics_and_canonical_paths() -> None:
    service = ResourceService()
    summary = service.get_resource_catalog_summary()

    assert summary.total_resources >= 4
    assert "RAG foundations" in summary.topics
    assert "intermediate" in summary.difficulties
    assert any(
        path.endswith("rag\\resources\\staging") or path.endswith("rag/resources/staging")
        for path in summary.canonical_paths
    )


def test_validate_seed_payload_maps_to_backend_contract() -> None:
    schema = load_resource_schema()
    payload = {
        "title": "Test Resource",
        "url": "https://example.com/pathai/test-resource",
        "type": "article",
        "topics": ["Testing"],
        "subtopics": ["schema validation"],
        "difficulty": "beginner",
        "estimated_time_minutes": 20,
        "source": "Example",
        "quality_score": 0.7,
        "access_label": "open",
        "foundational": False,
        "last_verified": "2026-06-09",
    }

    response = validate_seed_payload(payload, schema)

    assert response.valid is True
    assert response.mapped_resource is not None
    assert response.mapped_resource.source_domain == "example.com"


def test_loader_rejects_missing_resource_directory() -> None:
    with pytest.raises(ResourceSeedValidationError):
        load_resource_seeds_from_directory(
            Path("definitely_missing_resource_directory"),
            load_resource_schema(),
        )
