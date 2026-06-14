from typing import Annotated, Any

from fastapi import APIRouter, Body

from app.api.v1.runtime_services import build_runtime_services
from app.core.errors import PathAIError
from app.rag.errors import ResourceError
from app.rag.schemas import (
    CurriculumResourceAttachmentRequest,
    CurriculumResourceAttachmentResponse,
    ResourceCatalogSummary,
    ResourceRetrievalRequest,
    ResourceRetrievalResult,
    ResourceSeedValidationResponse,
)
from app.rag.service import ResourceService

router = APIRouter(prefix="/resources", tags=["resources"])
resource_service: ResourceService = build_runtime_services().resources


@router.get(
    "/catalog/summary",
    response_model=ResourceCatalogSummary,
    summary="Return the temporary curated resource catalog summary.",
)
async def get_resource_catalog_summary() -> ResourceCatalogSummary:
    try:
        return resource_service.get_resource_catalog_summary()
    except ResourceError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/retrieve",
    response_model=ResourceRetrievalResult,
    summary="Retrieve curated resources for one curriculum topic.",
)
async def retrieve_resources(request: ResourceRetrievalRequest) -> ResourceRetrievalResult:
    try:
        return resource_service.retrieve_for_topic(request)
    except ResourceError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/retrieve-for-curriculum",
    response_model=CurriculumResourceAttachmentResponse,
    summary="Attach curated resources to all topics in a curriculum payload.",
)
async def retrieve_resources_for_curriculum(
    request: CurriculumResourceAttachmentRequest,
) -> CurriculumResourceAttachmentResponse:
    try:
        return resource_service.retrieve_for_curriculum(request)
    except ResourceError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/validate-seed",
    response_model=ResourceSeedValidationResponse,
    summary="Validate a curated resource seed payload against the canonical seed contract.",
)
async def validate_resource_seed(
    payload: Annotated[dict[str, Any], Body(...)],
) -> ResourceSeedValidationResponse:
    try:
        return resource_service.validate_seed(payload)
    except ResourceError as exc:
        raise _to_pathai_error(exc) from exc


def _to_pathai_error(exc: ResourceError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
