from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

APPROVAL_THRESHOLD = 0.78
DEFAULT_REQUIRED_RESOURCES_PER_TOPIC = 2
DEFAULT_MAX_REVISIONS = 3

IssueSeverity = Literal["info", "warning", "critical"]
IssueCategory = Literal[
    "structure",
    "pacing",
    "prerequisite",
    "difficulty",
    "coverage",
    "resource_quality",
    "explanation",
    "personalization",
]
CriticDecisionStatus = Literal["approved", "rejected", "auto_approved"]
CriticReviewSource = Literal["deterministic", "mock_llm"]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_review_id() -> str:
    return str(uuid4())
