from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import KnowledgeMapServiceDependency
from app.schemas.ids import KnowledgeMapId
from app.schemas.knowledge_map import KnowledgeMapDTO

router = APIRouter(prefix="/knowledge-maps", tags=["knowledge-maps"])


@router.get("/{knowledge_map_id}", response_model=KnowledgeMapDTO)
def get_knowledge_map(
    knowledge_map_id: KnowledgeMapId,
    service: KnowledgeMapServiceDependency,
) -> KnowledgeMapDTO:
    return service.get_by_id(knowledge_map_id)
