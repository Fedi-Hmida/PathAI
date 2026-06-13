from datetime import datetime

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.models.common import AccessType, DifficultyLevel, ResourceType, new_uuid, utc_now


class ResourceDocument(Document):
    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(default_factory=new_uuid)
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
    embedding: list[float] = Field(default_factory=list)
    active: bool = True
    last_verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "resources"
        indexes = [
            IndexModel([("resource_id", ASCENDING)], unique=True),
            IndexModel([("topics", ASCENDING), ("difficulty", ASCENDING)]),
            IndexModel([("type", ASCENDING)]),
            IndexModel([("quality_score", DESCENDING)]),
            IndexModel([("active", ASCENDING)]),
        ]
