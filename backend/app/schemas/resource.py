from __future__ import annotations

from pydantic import Field

from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import (
    DifficultyLevel,
    ResourceAttachmentStatus,
    ResourceStatus,
    ResourceType,
)
from app.schemas.ids import AttachmentId, ConceptId, CurriculumId, GoalId, ResourceId, TopicId
from app.schemas.knowledge_map import KnowledgeMapDTO


class ResourceSeedItem(BaseSchema):
    resource_id: ResourceId
    title: str = Field(min_length=1, max_length=240)
    resource_type: ResourceType
    source_name: str = Field(min_length=1, max_length=160)
    url: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1, max_length=1000)
    topic_tags: list[str] = Field(min_length=1, max_length=20)
    concept_ids: list[ConceptId] = Field(min_length=1, max_length=12)
    difficulty: DifficultyLevel
    estimated_minutes: int = Field(ge=1, le=600)
    quality_score: Score
    freshness_score: Score | None = None
    license_note: str = Field(min_length=1, max_length=300)
    language: str = Field(default="en", min_length=2, max_length=12)


class ResourceDTO(TimestampedDTO, VersionedDTO):
    resource_id: ResourceId
    title: str = Field(min_length=1, max_length=240)
    resource_type: ResourceType
    source_name: str = Field(min_length=1, max_length=160)
    url: str = Field(min_length=1, max_length=500)
    topic_tags: list[str] = Field(min_length=1, max_length=20)
    concept_ids: list[ConceptId] = Field(min_length=1, max_length=12)
    difficulty: DifficultyLevel
    estimated_minutes: int = Field(ge=1, le=600)
    quality_score: Score
    license_note: str = Field(min_length=1, max_length=300)
    status: ResourceStatus = ResourceStatus.ACTIVE
    summary: str | None = Field(default=None, max_length=1000)
    author: str | None = Field(default=None, max_length=160)
    published_year: int | None = Field(default=None, ge=1900, le=2100)
    language: str = Field(default="en", min_length=2, max_length=12)
    freshness_score: Score | None = None


class ResourceAttachmentDTO(TimestampedDTO, VersionedDTO):
    attachment_id: AttachmentId
    goal_id: GoalId
    curriculum_id: CurriculumId
    topic_id: TopicId
    resource_id: ResourceId
    rank: int = Field(ge=1, le=20)
    relevance_score: Score
    selection_reason: str = Field(min_length=1, max_length=800)
    quality_score_snapshot: Score | None = None
    diversity_category: str | None = Field(default=None, max_length=120)
    status: ResourceAttachmentStatus = ResourceAttachmentStatus.ACTIVE
    warnings: list[str] = Field(default_factory=list, max_length=10)


class ResourceCoverageSummary(BaseSchema):
    topics_with_resources: int = Field(ge=0)
    topics_without_resources: int = Field(ge=0)
    average_relevance: Score
    resource_type_diversity: Score


class ResourceFilter(BaseSchema):
    topic_tags: list[str] = Field(default_factory=list, max_length=20)
    concept_ids: list[ConceptId] = Field(default_factory=list, max_length=12)
    difficulty: DifficultyLevel | None = None
    resource_types: list[ResourceType] = Field(default_factory=list, max_length=8)


class ResourceAgentInput(BaseSchema):
    curriculum: CurriculumDTO
    knowledge_map: KnowledgeMapDTO
    corpus_resources: list[ResourceDTO] = Field(min_length=1)
    max_resources_per_topic: int = Field(default=3, ge=1, le=10)


class ResourceAgentOutput(BaseSchema):
    attachments: list[ResourceAttachmentDTO] = Field(default_factory=list)
    coverage_summary: ResourceCoverageSummary
    warnings: list[str] = Field(default_factory=list, max_length=20)
