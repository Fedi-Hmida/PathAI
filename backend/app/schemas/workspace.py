from __future__ import annotations

from app.schemas.base import BaseSchema
from app.schemas.ids import CurriculumId, KnowledgeMapId, RunId


class WorkspaceRef(BaseSchema):
    """Pointer to a user's workspace, identified by its orchestration run."""

    run_id: RunId


class WorkspaceGenerationResult(BaseSchema):
    """Pointer to the caller's freshly regenerated knowledge map + curriculum."""

    knowledge_map_id: KnowledgeMapId
    curriculum_id: CurriculumId
