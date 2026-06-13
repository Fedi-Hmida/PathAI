import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.rag.constants import resource_approved_path, resource_schema_path, resource_staging_path
from app.rag.resource_loader import (
    load_json_object,
    load_resource_seeds_from_directories,
    validate_resource_seed_against_json_schema,
)
from app.rag.schemas import (
    ResourceCatalogItem,
    ResourceSeed,
    ResourceSeedValidationResponse,
    seed_to_resource_document_payload,
)


def canonical_resource_directories(
    include_staging: bool = True,
    include_approved: bool = True,
) -> list[Path]:
    directories: list[Path] = []
    if include_staging:
        directories.append(resource_staging_path())
    if include_approved:
        directories.append(resource_approved_path())
    return directories


def load_resource_schema() -> dict[str, Any]:
    return load_json_object(resource_schema_path())


def load_canonical_resource_seeds(
    include_staging: bool = True,
    include_approved: bool = True,
) -> list[ResourceSeed]:
    schema = load_resource_schema()
    return load_resource_seeds_from_directories(
        canonical_resource_directories(
            include_staging=include_staging,
            include_approved=include_approved,
        ),
        schema,
    )


def build_catalog_items_from_seeds(seeds: list[ResourceSeed]) -> list[ResourceCatalogItem]:
    items_by_url: dict[str, ResourceCatalogItem] = {}
    for seed in seeds:
        payload = seed_to_resource_document_payload(seed)
        item = ResourceCatalogItem(
            resource_id=resource_id_for_url(payload.url),
            **payload.model_dump(),
        )
        existing = items_by_url.get(item.url)
        if existing is None or item.quality_score > existing.quality_score:
            items_by_url[item.url] = item
    return sorted(items_by_url.values(), key=lambda item: item.title.lower())


def validate_seed_payload(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any] | None = None,
) -> ResourceSeedValidationResponse:
    resource_schema = schema or load_resource_schema()
    validate_resource_seed_against_json_schema(payload, resource_schema)
    seed = ResourceSeed.model_validate(payload)
    mapped = seed_to_resource_document_payload(seed)
    return ResourceSeedValidationResponse(
        valid=True,
        message="Resource seed payload is valid and maps to the backend resource contract.",
        mapped_resource=mapped,
    )


def resource_id_for_url(url: str) -> str:
    digest = hashlib.sha1(url.strip().lower().encode("utf-8")).hexdigest()[:16]
    return f"res_{digest}"
