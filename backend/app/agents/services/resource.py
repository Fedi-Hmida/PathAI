from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import ResourceAgent
from app.agents.services.common import create_or_get, create_or_replace, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.resource import ResourceAgentInput, ResourceAgentOutput, ResourceAttachmentDTO
from app.services import ResourceService


@dataclass(slots=True)
class ResourceAgentService:
    agent: ResourceAgent
    resources: ResourceService

    def attach(
        self,
        curriculum: CurriculumDTO,
        knowledge_map: KnowledgeMapDTO,
    ) -> list[ResourceAttachmentDTO]:
        corpus = [
            create_or_get(
                create=self.resources.create_resource,
                get=self.resources.get_resource_by_id,
                record=resource,
                record_id=resource.resource_id,
            )
            for resource in demo.RESOURCE_CORPUS
        ]
        payload = ResourceAgentInput(
            curriculum=curriculum,
            knowledge_map=knowledge_map,
            corpus_resources=corpus,
            max_resources_per_topic=3,
        )
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=ResourceAgentOutput,
            payload=self.agent.attach_resources(payload),
        )
        # Each attachment's ID is now goal+topic+resource-scoped
        # (`deterministic/resource.py::_attachment_id`), so a repeat call for
        # the same goal recomputes the same IDs - overwrite in place with
        # create_or_replace rather than keeping a stale create_or_get hit, the
        # same regeneration-freshness fix already applied to Progress/Critic.
        return [
            create_or_replace(
                create=self.resources.create_attachment,
                save=self.resources.save_attachment,
                record=attachment,
            )
            for attachment in output.attachments
        ]
