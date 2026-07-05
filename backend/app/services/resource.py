from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.resource import ResourceRepository
from app.schemas.enums import ResourceAttachmentStatus, ResourceStatus
from app.schemas.ids import AttachmentId, CurriculumId, GoalId, ResourceId, TopicId
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO


@dataclass(slots=True)
class ResourceService:
    repository: ResourceRepository

    def create_resource(self, resource: ResourceDTO) -> ResourceDTO:
        return self.repository.create_resource(resource)

    def save_resource(self, resource: ResourceDTO) -> ResourceDTO:
        return self.repository.save_resource(resource)

    def get_resource_by_id(self, resource_id: ResourceId) -> ResourceDTO:
        return self.repository.get_resource_by_id(resource_id)

    def list_resources(self) -> list[ResourceDTO]:
        return self.repository.list_resources()

    def update_resource_status(
        self,
        resource_id: ResourceId,
        status: ResourceStatus,
    ) -> ResourceDTO:
        return self.repository.update_resource_status(resource_id, status)

    def create_attachment(self, attachment: ResourceAttachmentDTO) -> ResourceAttachmentDTO:
        return self.repository.create_attachment(attachment)

    def save_attachment(self, attachment: ResourceAttachmentDTO) -> ResourceAttachmentDTO:
        return self.repository.save_attachment(attachment)

    def get_attachment_by_id(self, attachment_id: AttachmentId) -> ResourceAttachmentDTO:
        return self.repository.get_attachment_by_id(attachment_id)

    def list_attachments_by_goal_id(self, goal_id: GoalId) -> list[ResourceAttachmentDTO]:
        return self.repository.list_attachments_by_goal_id(goal_id)

    def list_attachments_by_curriculum_id(
        self,
        curriculum_id: CurriculumId,
    ) -> list[ResourceAttachmentDTO]:
        return self.repository.list_attachments_by_curriculum_id(curriculum_id)

    def list_attachments_by_topic_id(self, topic_id: TopicId) -> list[ResourceAttachmentDTO]:
        return self.repository.list_attachments_by_topic_id(topic_id)

    def update_attachment_status(
        self,
        attachment_id: AttachmentId,
        status: ResourceAttachmentStatus,
    ) -> ResourceAttachmentDTO:
        return self.repository.update_attachment_status(attachment_id, status)
