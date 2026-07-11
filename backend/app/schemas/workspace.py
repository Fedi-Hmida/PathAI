from __future__ import annotations

from app.schemas.base import BaseSchema
from app.schemas.ids import RunId


class WorkspaceRef(BaseSchema):
    """Pointer to a user's workspace, identified by its orchestration run."""

    run_id: RunId
