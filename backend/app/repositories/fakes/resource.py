from __future__ import annotations

from app.repositories.fakes.base import InMemoryStore
from app.schemas.enums import ResourceAttachmentStatus, ResourceStatus
from app.schemas.ids import AttachmentId, CurriculumId, GoalId, ResourceId, TopicId
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO


class FakeResourceRepository:
    def __init__(self) -> None:
        self._resources: InMemoryStore[ResourceDTO] = InMemoryStore("resource")
        self._attachments: InMemoryStore[ResourceAttachmentDTO] = InMemoryStore(
            "resource attachment",
        )

    def create_resource(self, resource: ResourceDTO) -> ResourceDTO:
        return self._resources.create(resource.resource_id, resource)

    def save_resource(self, resource: ResourceDTO) -> ResourceDTO:
        return self._resources.save(resource.resource_id, resource)

    def get_resource_by_id(self, resource_id: ResourceId) -> ResourceDTO:
        return self._resources.get(resource_id)

    def list_resources(self) -> list[ResourceDTO]:
        return self._resources.list_all()

    def update_resource_status(
        self,
        resource_id: ResourceId,
        status: ResourceStatus,
    ) -> ResourceDTO:
        return self._resources.update_fields(resource_id, status=status)

    def create_attachment(
        self,
        attachment: ResourceAttachmentDTO,
    ) -> ResourceAttachmentDTO:
        return self._attachments.create(attachment.attachment_id, attachment)

    def save_attachment(
        self,
        attachment: ResourceAttachmentDTO,
    ) -> ResourceAttachmentDTO:
        return self._attachments.save(attachment.attachment_id, attachment)

    def get_attachment_by_id(self, attachment_id: AttachmentId) -> ResourceAttachmentDTO:
        return self._attachments.get(attachment_id)

    def list_attachments_by_goal_id(self, goal_id: GoalId) -> list[ResourceAttachmentDTO]:
        return self._attachments.list_where("goal_id", goal_id)

    def list_attachments_by_curriculum_id(
        self,
        curriculum_id: CurriculumId,
    ) -> list[ResourceAttachmentDTO]:
        return self._attachments.list_where("curriculum_id", curriculum_id)

    def list_attachments_by_topic_id(self, topic_id: TopicId) -> list[ResourceAttachmentDTO]:
        return self._attachments.list_where("topic_id", topic_id)

    def update_attachment_status(
        self,
        attachment_id: AttachmentId,
        status: ResourceAttachmentStatus,
    ) -> ResourceAttachmentDTO:
        return self._attachments.update_fields(attachment_id, status=status)

    def clear(self) -> None:
        self._resources.clear()
        self._attachments.clear()
