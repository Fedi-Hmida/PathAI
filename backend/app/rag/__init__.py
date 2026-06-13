"""Backend RAG package."""

from app.rag.resource_loader import (
    ResourceSeedValidationError,
    load_json_object,
    load_resource_seed,
    load_resource_seeds_from_directories,
    load_resource_seeds_from_directory,
    map_seed_to_document_payload,
    validate_resource_seed_against_json_schema,
)
from app.rag.schemas import (
    CurriculumResourceAttachmentRequest,
    CurriculumResourceAttachmentResponse,
    ResourceCatalogItem,
    ResourceCatalogSummary,
    ResourceDocumentPayload,
    ResourceRetrievalRequest,
    ResourceRetrievalResult,
    ResourceSeed,
    seed_to_resource_document_payload,
)
from app.rag.service import ResourceCatalog, ResourceService

__all__ = [
    "CurriculumResourceAttachmentRequest",
    "CurriculumResourceAttachmentResponse",
    "ResourceCatalog",
    "ResourceCatalogItem",
    "ResourceCatalogSummary",
    "ResourceDocumentPayload",
    "ResourceRetrievalRequest",
    "ResourceRetrievalResult",
    "ResourceSeed",
    "ResourceSeedValidationError",
    "ResourceService",
    "load_json_object",
    "load_resource_seed",
    "load_resource_seeds_from_directories",
    "load_resource_seeds_from_directory",
    "map_seed_to_document_payload",
    "seed_to_resource_document_payload",
    "validate_resource_seed_against_json_schema",
]
