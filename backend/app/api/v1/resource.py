from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    ResourceServiceDependency,
)
from app.schemas.ids import CurriculumId, ResourceId
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/by-curriculum/{curriculum_id}", response_model=list[ResourceAttachmentDTO])
def list_resources_by_curriculum(
    curriculum_id: CurriculumId,
    service: ResourceServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> list[ResourceAttachmentDTO]:
    attachments = service.list_attachments_by_curriculum_id(curriculum_id)
    # Attachments are per-workspace; authorize via their owning goal (all
    # attachments of one curriculum share a goal). An empty list belongs to
    # no one and leaks nothing.
    if attachments:
        authz.assert_goal_access(current_user, attachments[0].goal_id)
    return attachments


# NOTE: /resources/{resource_id} returns the shared curated corpus, which is
# global reference data with no owner, so it is intentionally not scoped.
@router.get("/{resource_id}", response_model=ResourceDTO)
def get_resource(resource_id: ResourceId, service: ResourceServiceDependency) -> ResourceDTO:
    return service.get_resource_by_id(resource_id)
