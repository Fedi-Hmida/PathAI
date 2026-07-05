from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import ResourceServiceDependency
from app.schemas.ids import CurriculumId, ResourceId
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/by-curriculum/{curriculum_id}", response_model=list[ResourceAttachmentDTO])
def list_resources_by_curriculum(
    curriculum_id: CurriculumId,
    service: ResourceServiceDependency,
) -> list[ResourceAttachmentDTO]:
    return service.list_attachments_by_curriculum_id(curriculum_id)


@router.get("/{resource_id}", response_model=ResourceDTO)
def get_resource(resource_id: ResourceId, service: ResourceServiceDependency) -> ResourceDTO:
    return service.get_resource_by_id(resource_id)
