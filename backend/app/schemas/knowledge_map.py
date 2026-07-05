from __future__ import annotations

from pydantic import Field

from app.schemas.assessment import AssessmentAnswerDTO, ConceptEvidence
from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.enums import ConceptClassification, KnowledgeMapStatus
from app.schemas.ids import AssessmentId, ConceptId, GoalId, KnowledgeMapId, RunId


class ConceptMasteryDTO(BaseSchema):
    concept_id: ConceptId
    label: str = Field(min_length=1, max_length=160)
    mastery_score: Score
    classification: ConceptClassification
    evidence: list[str] = Field(default_factory=list, max_length=12)
    prerequisites: list[ConceptId] = Field(default_factory=list, max_length=12)
    recommended_action: str | None = Field(default=None, max_length=300)
    confidence: Score | None = None


class KnowledgeMapCreate(BaseSchema):
    goal_id: GoalId
    assessment_session_id: AssessmentId
    run_id: RunId
    concepts: list[ConceptMasteryDTO] = Field(min_length=1)
    strong_concepts: list[ConceptId] = Field(default_factory=list)
    developing_concepts: list[ConceptId] = Field(default_factory=list)
    weak_concepts: list[ConceptId] = Field(default_factory=list)
    missing_concepts: list[ConceptId] = Field(default_factory=list)
    confidence: Score
    summary: str = Field(min_length=1, max_length=1000)


class KnowledgeMapDTO(TimestampedDTO, VersionedDTO):
    knowledge_map_id: KnowledgeMapId
    goal_id: GoalId
    assessment_session_id: AssessmentId
    run_id: RunId
    status: KnowledgeMapStatus
    concepts: list[ConceptMasteryDTO] = Field(min_length=1)
    strong_concepts: list[ConceptId] = Field(default_factory=list)
    developing_concepts: list[ConceptId] = Field(default_factory=list)
    weak_concepts: list[ConceptId] = Field(default_factory=list)
    missing_concepts: list[ConceptId] = Field(default_factory=list)
    confidence: Score
    summary: str = Field(min_length=1, max_length=1000)
    warnings: list[str] = Field(default_factory=list, max_length=20)


class KnowledgeMapAgentInput(BaseSchema):
    goal_text: str = Field(min_length=5, max_length=500)
    assessment_answers: list[AssessmentAnswerDTO] = Field(default_factory=list)
    concept_evidence: list[ConceptEvidence] = Field(min_length=1)


class KnowledgeMapAgentOutput(BaseSchema):
    concepts: list[ConceptMasteryDTO] = Field(min_length=1)
    strong_concepts: list[ConceptId] = Field(default_factory=list)
    developing_concepts: list[ConceptId] = Field(default_factory=list)
    weak_concepts: list[ConceptId] = Field(default_factory=list)
    missing_concepts: list[ConceptId] = Field(default_factory=list)
    confidence: Score
    summary: str = Field(min_length=1, max_length=1000)
