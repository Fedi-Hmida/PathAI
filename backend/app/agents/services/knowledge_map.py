from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import KnowledgeMapAgent
from app.agents.services.common import create_or_get, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.assessment import AssessmentAnswerDTO, AssessmentSessionDTO
from app.schemas.enums import KnowledgeMapStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import (
    KnowledgeMapAgentInput,
    KnowledgeMapAgentOutput,
    KnowledgeMapDTO,
)
from app.services import KnowledgeMapService


@dataclass(slots=True)
class KnowledgeMapAgentService:
    agent: KnowledgeMapAgent
    knowledge_maps: KnowledgeMapService

    def build(
        self,
        goal: LearningGoalDTO,
        assessment: AssessmentSessionDTO,
        answers: list[AssessmentAnswerDTO],
    ) -> KnowledgeMapDTO:
        payload = KnowledgeMapAgentInput(
            goal_text=goal.goal_text,
            assessment_answers=answers,
            concept_evidence=assessment.concept_evidence,
        )
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=KnowledgeMapAgentOutput,
            payload=self.agent.build_knowledge_map(payload),
        )
        knowledge_map = KnowledgeMapDTO(
            knowledge_map_id=demo.KNOWLEDGE_MAP_ID,
            goal_id=goal.goal_id,
            assessment_session_id=assessment.assessment_session_id,
            run_id=goal.run_id,
            status=KnowledgeMapStatus.ACTIVE,
            concepts=output.concepts,
            strong_concepts=output.strong_concepts,
            developing_concepts=output.developing_concepts,
            weak_concepts=output.weak_concepts,
            missing_concepts=output.missing_concepts,
            confidence=output.confidence,
            summary=output.summary,
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        return create_or_get(
            create=self.knowledge_maps.create,
            get=self.knowledge_maps.get_by_id,
            record=knowledge_map,
            record_id=knowledge_map.knowledge_map_id,
        )
