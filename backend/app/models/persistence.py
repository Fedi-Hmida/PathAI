from datetime import datetime
from typing import Any

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.models.common import utc_now


class ProgressSummaryDocument(Document):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "progress_summaries"
        indexes = [
            IndexModel([("curriculum_id", ASCENDING)], unique=True),
            IndexModel([("updated_at", DESCENDING)]),
        ]


class QuizSnapshotDocument(Document):
    model_config = ConfigDict(extra="forbid")

    quiz_id: str = Field(min_length=1, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "quiz_snapshots"
        indexes = [
            IndexModel([("quiz_id", ASCENDING)], unique=True),
            IndexModel([("curriculum_id", ASCENDING), ("created_at", DESCENDING)]),
        ]


class QuizAttemptDocument(Document):
    model_config = ConfigDict(extra="forbid")

    attempt_id: str = Field(min_length=1, max_length=120)
    quiz_id: str = Field(min_length=1, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    submitted_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "quiz_attempts"
        indexes = [
            IndexModel([("attempt_id", ASCENDING)], unique=True),
            IndexModel([("quiz_id", ASCENDING), ("submitted_at", DESCENDING)]),
            IndexModel([("curriculum_id", ASCENDING), ("submitted_at", DESCENDING)]),
        ]


class AdaptationResultDocument(Document):
    model_config = ConfigDict(extra="forbid")

    adaptation_id: str = Field(min_length=1, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "adaptation_results"
        indexes = [
            IndexModel([("adaptation_id", ASCENDING)], unique=True),
            IndexModel([("curriculum_id", ASCENDING), ("created_at", DESCENDING)]),
        ]


class CriticReviewDocument(Document):
    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(min_length=1, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "critic_reviews"
        indexes = [
            IndexModel([("review_id", ASCENDING)], unique=True),
            IndexModel([("curriculum_id", ASCENDING), ("created_at", DESCENDING)]),
        ]


class ResourceAttachmentDocument(Document):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "resource_attachments"
        indexes = [
            IndexModel([("curriculum_id", ASCENDING)], unique=True),
            IndexModel([("updated_at", DESCENDING)]),
        ]


class EvaluationReportDocument(Document):
    model_config = ConfigDict(extra="forbid")

    evaluation_id: str = Field(min_length=1, max_length=120)
    dataset_name: str = Field(min_length=1, max_length=180)
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "evaluation_reports"
        indexes = [
            IndexModel([("evaluation_id", ASCENDING)], unique=True),
            IndexModel([("dataset_name", ASCENDING), ("created_at", DESCENDING)]),
        ]
