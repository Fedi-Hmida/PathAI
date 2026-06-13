from datetime import UTC, date, datetime, time
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.curriculum.schemas import CurriculumPlan
from app.models.common import AccessType, DifficultyLevel, ResourceType
from app.rag.constants import DEFAULT_RESOURCE_TOP_K, MAX_RESOURCE_TOP_K, RetrievalSource

ResourceSeedType = Literal["video", "paper", "docs", "course", "article"]
ResourceAccessLabel = Literal["open", "requires_free_account", "university_access", "restricted"]

RESOURCE_TYPE_MAP: dict[ResourceSeedType, ResourceType] = {
    "article": "article",
    "course": "course",
    "docs": "documentation",
    "paper": "paper",
    "video": "video",
}

ACCESS_LABEL_MAP: dict[ResourceAccessLabel, AccessType] = {
    "open": "free",
    "requires_free_account": "free",
    "restricted": "unknown",
    "university_access": "institutional",
}


class ResourceSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=240)
    url: str = Field(min_length=1, max_length=2000)
    type: ResourceSeedType
    topics: list[str] = Field(min_length=1)
    subtopics: list[str] = Field(default_factory=list)
    difficulty: DifficultyLevel
    estimated_time_minutes: int = Field(ge=1, le=600)
    source: str = Field(min_length=1, max_length=120)
    quality_score: float = Field(ge=0.0, le=1.0)
    access_label: ResourceAccessLabel
    foundational: bool
    last_verified: date
    license: str | None = Field(default=None, max_length=120)

    @field_validator("url")
    @classmethod
    def require_http_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Resource URL must be an absolute HTTP(S) URL.")
        return value

    @field_validator("topics", "subtopics")
    @classmethod
    def normalize_non_empty_strings(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Resource topics and subtopics cannot contain empty strings.")
        return normalized

    def to_resource_document_payload(self) -> "ResourceDocumentPayload":
        return ResourceDocumentPayload(
            title=self.title,
            url=self.url,
            type=RESOURCE_TYPE_MAP[self.type],
            topics=self.topics,
            subtopics=self.subtopics,
            difficulty=self.difficulty,
            estimated_minutes=self.estimated_time_minutes,
            source_name=self.source,
            source_domain=source_domain_from_url(self.url),
            quality_score=self.quality_score,
            access=ACCESS_LABEL_MAP[self.access_label],
            license=self.license,
            foundational=self.foundational,
            last_verified_at=datetime.combine(self.last_verified, time.min, tzinfo=UTC),
        )


class ResourceDocumentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=240)
    url: str = Field(min_length=1, max_length=2000)
    type: ResourceType
    topics: list[str] = Field(default_factory=list)
    subtopics: list[str] = Field(default_factory=list)
    difficulty: DifficultyLevel
    estimated_minutes: int = Field(ge=1, le=600)
    source_name: str = Field(min_length=1, max_length=120)
    source_domain: str | None = Field(default=None, max_length=120)
    quality_score: float = Field(ge=0.0, le=1.0)
    access: AccessType = "free"
    license: str | None = Field(default=None, max_length=120)
    foundational: bool = False
    last_verified_at: datetime | None = None


def seed_to_resource_document_payload(seed: ResourceSeed) -> ResourceDocumentPayload:
    return seed.to_resource_document_payload()


def source_domain_from_url(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc.removeprefix("www.")


class ResourceCatalogItem(ResourceDocumentPayload):
    resource_id: str = Field(min_length=1, max_length=120)


class ResourceMatchExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_overlap: list[str] = Field(default_factory=list)
    subtopic_overlap: list[str] = Field(default_factory=list)
    difficulty_fit: str = Field(min_length=1, max_length=120)
    quality_signal: str = Field(min_length=1, max_length=200)
    access_signal: str = Field(min_length=1, max_length=200)
    notes: list[str] = Field(default_factory=list, max_length=6)


class ResourceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource: ResourceCatalogItem
    match_score: float = Field(ge=0.0, le=1.0)
    topic_score: float = Field(ge=0.0, le=1.0)
    subtopic_score: float = Field(ge=0.0, le=1.0)
    difficulty_score: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)
    retrieval_source: RetrievalSource
    why_this: str = Field(min_length=1, max_length=500)
    explanation: ResourceMatchExplanation


class ResourceRetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1, max_length=180)
    goal: str | None = Field(default=None, min_length=3, max_length=1000)
    difficulty: DifficultyLevel = "beginner"
    subtopics: list[str] = Field(default_factory=list, max_length=12)
    knowledge_map: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=DEFAULT_RESOURCE_TOP_K, ge=1, le=MAX_RESOURCE_TOP_K)
    include_foundational_fallback: bool = True

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("subtopics")
    @classmethod
    def normalize_subtopics(cls, values: list[str]) -> list[str]:
        return [" ".join(value.strip().split()) for value in values if value.strip()]


class ResourceRetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: ResourceRetrievalRequest
    candidates: list[ResourceCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResourceRerankRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str | None = Field(default=None, min_length=3, max_length=1000)
    topic: str = Field(min_length=1, max_length=180)
    difficulty: DifficultyLevel
    knowledge_map: dict[str, Any] = Field(default_factory=dict)
    candidates: list[ResourceCandidate] = Field(default_factory=list)
    top_k: int = Field(default=DEFAULT_RESOURCE_TOP_K, ge=1, le=MAX_RESOURCE_TOP_K)


class ResourceRerankedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1, max_length=120)
    rank: int = Field(ge=1, le=MAX_RESOURCE_TOP_K)
    score: float = Field(ge=0.0, le=1.0)
    why_this: str = Field(min_length=1, max_length=500)


class ResourceRerankResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1, max_length=180)
    ranked_candidates: list[ResourceRerankedCandidate] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=700)
    used_mock_llm: bool = False


class ResourceReferencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    url: str = Field(min_length=1, max_length=2000)
    type: ResourceType
    source_name: str | None = Field(default=None, max_length=120)
    source_domain: str | None = Field(default=None, max_length=120)
    difficulty: DifficultyLevel
    estimated_minutes: int = Field(ge=1, le=600)
    quality_score: float = Field(ge=0.0, le=1.0)
    access: AccessType = "free"
    why_recommended: str = Field(min_length=1, max_length=500)


class TopicResourceAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: str
    topic: str
    resources: list[ResourceReferencePayload] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CurriculumResourceAttachmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan
    top_k: int = Field(default=2, ge=1, le=MAX_RESOURCE_TOP_K)
    include_foundational_fallback: bool = True


class CurriculumResourceAttachmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str
    enriched_curriculum: dict[str, Any]
    topic_results: list[ResourceRetrievalResult] = Field(default_factory=list)
    attachments: list[TopicResourceAttachment] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResourceCatalogSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_resources: int
    topics: list[str] = Field(default_factory=list)
    difficulties: list[DifficultyLevel] = Field(default_factory=list)
    resource_types: list[ResourceType] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    canonical_paths: list[str] = Field(default_factory=list)


class ResourceSeedValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    message: str
    mapped_resource: ResourceDocumentPayload | None = None


class ResourceExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ResourceCatalogSummary
    retrieval: ResourceRetrievalResult
