from __future__ import annotations

from typing import Protocol

from app.schemas.enums import ResourceAttachmentStatus, ResourceStatus
from app.schemas.ids import AttachmentId, CurriculumId, GoalId, ResourceId, TopicId
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO


class ResourceRepository(Protocol):
    def create_resource(self, resource: ResourceDTO) -> ResourceDTO: ...

    def save_resource(self, resource: ResourceDTO) -> ResourceDTO: ...

    def get_resource_by_id(self, resource_id: ResourceId) -> ResourceDTO: ...

    def list_resources(self) -> list[ResourceDTO]: ...

    def update_resource_status(
        self,
        resource_id: ResourceId,
        status: ResourceStatus,
    ) -> ResourceDTO: ...

    def create_attachment(
        self,
        attachment: ResourceAttachmentDTO,
    ) -> ResourceAttachmentDTO: ...

    def save_attachment(
        self,
        attachment: ResourceAttachmentDTO,
    ) -> ResourceAttachmentDTO: ...

    def get_attachment_by_id(self, attachment_id: AttachmentId) -> ResourceAttachmentDTO: ...

    def list_attachments_by_goal_id(self, goal_id: GoalId) -> list[ResourceAttachmentDTO]: ...

    def list_attachments_by_curriculum_id(
        self,
        curriculum_id: CurriculumId,
    ) -> list[ResourceAttachmentDTO]: ...

    def list_attachments_by_topic_id(self, topic_id: TopicId) -> list[ResourceAttachmentDTO]: ...

    def update_attachment_status(
        self,
        attachment_id: AttachmentId,
        status: ResourceAttachmentStatus,
    ) -> ResourceAttachmentDTO: ...

    def clear(self) -> None: ...
